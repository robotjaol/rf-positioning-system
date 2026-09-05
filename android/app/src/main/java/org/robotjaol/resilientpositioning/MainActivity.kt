package org.robotjaol.resilientpositioning

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.os.Bundle
import android.provider.Settings
import android.view.Gravity
import android.widget.*
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

class MainActivity : Activity() {
    private lateinit var collector: TelemetryCollector
    private lateinit var status: TextView
    private lateinit var endpoint: EditText
    private val worker = Executors.newSingleThreadExecutor()
    @Volatile private var streaming = false
    private val deviceId by lazy { Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID) ?: "android-phone" }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        collector = TelemetryCollector(this)
        buildUi()
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION), 10)
        }
    }

    private fun buildUi() {
        val root = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(32,48,32,32); gravity=Gravity.CENTER_HORIZONTAL }
        root.addView(TextView(this).apply { text="Resilient Positioning"; textSize=26f })
        root.addView(TextView(this).apply { text="GNSS + IMU + Wi-Fi + cellular telemetry"; textSize=14f })
        endpoint = EditText(this).apply { hint="Laptop endpoint"; setText("http://192.168.1.10:8000") }
        root.addView(endpoint, LinearLayout.LayoutParams(-1,-2).apply { topMargin=36 })
        val button = Button(this).apply { text="Start streaming" }
        root.addView(button, LinearLayout.LayoutParams(-1,-2).apply { topMargin=16 })
        status = TextView(this).apply { text="Idle"; textSize=15f }
        root.addView(status, LinearLayout.LayoutParams(-1,-2).apply { topMargin=24 })
        button.setOnClickListener {
            if (!streaming) {
                if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
                    requestPermissions(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION), 10)
                    return@setOnClickListener
                }
                streaming=true; button.text="Stop streaming"; collector.start(); streamLoop()
            } else {
                streaming=false; button.text="Start streaming"; collector.stop(); status.text="Stopped"
            }
        }
        setContentView(root)
    }

    private fun streamLoop() {
        worker.execute {
            while (streaming) {
                val body = collector.snapshot(deviceId).toString()
                val result = runCatching { post(endpoint.text.toString().trim(), body) }.fold({ "Connected: HTTP $it" }, { "Send failed: ${it.message}" })
                runOnUiThread { status.text = result }
                Thread.sleep(1000)
            }
        }
    }

    private fun post(baseUrl: String, body: String): Int {
        val c = URL(baseUrl.trimEnd('/') + "/v1/telemetry").openConnection() as HttpURLConnection
        c.requestMethod="POST"; c.connectTimeout=2500; c.readTimeout=2500; c.doOutput=true; c.setRequestProperty("Content-Type","application/json")
        c.outputStream.use { it.write(body.toByteArray()) }
        val code=c.responseCode
        (if(code in 200..299)c.inputStream else c.errorStream)?.use { it.readBytes() }
        c.disconnect(); return code
    }

    override fun onDestroy() {
        streaming=false
        runCatching { collector.stop() }
        worker.shutdownNow()
        super.onDestroy()
    }
}

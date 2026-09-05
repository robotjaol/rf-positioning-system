package org.robotjaol.resilientpositioning

import android.annotation.SuppressLint
import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.GnssMeasurement
import android.location.GnssMeasurementsEvent
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.net.wifi.WifiManager
import android.os.Bundle
import android.telephony.*
import org.json.JSONArray
import org.json.JSONObject

class TelemetryCollector(private val context: Context) : SensorEventListener, LocationListener {
    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
    private val wifiManager = context.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
    private val telephonyManager = context.getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager

    @Volatile private var location: Location? = null
    @Volatile private var accelEnu = floatArrayOf(0f, 0f, 0f)
    @Volatile private var gyro = floatArrayOf(0f, 0f, 0f)
    @Volatile private var pressureHpa: Float? = null
    @Volatile private var rotation = FloatArray(9).also { it[0]=1f; it[4]=1f; it[8]=1f }
    @Volatile private var rawGnss = JSONArray()
    @Volatile private var gnssClock: JSONObject? = null
    private var lastWifiScanMs = 0L

    private val gnssCallback = object : GnssMeasurementsEvent.Callback() {
        override fun onGnssMeasurementsReceived(event: GnssMeasurementsEvent) {
            val arr = JSONArray()
            event.measurements.take(64).forEach { m -> arr.put(measurementJson(m)) }
            rawGnss = arr
            gnssClock = JSONObject().apply {
                put("time_nanos", event.clock.timeNanos)
                if (event.clock.hasFullBiasNanos()) put("full_bias_nanos", event.clock.fullBiasNanos)
                if (event.clock.hasBiasNanos()) put("bias_nanos", event.clock.biasNanos)
            }
        }
    }

    @SuppressLint("MissingPermission")
    fun start() {
        locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 500L, 0f, this)
        locationManager.registerGnssMeasurementsCallback(context.mainExecutor, gnssCallback)
        listOf(Sensor.TYPE_LINEAR_ACCELERATION, Sensor.TYPE_GYROSCOPE, Sensor.TYPE_ROTATION_VECTOR, Sensor.TYPE_PRESSURE).forEach { type ->
            sensorManager.getDefaultSensor(type)?.let { sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME) }
        }
    }

    fun stop() {
        locationManager.removeUpdates(this)
        locationManager.unregisterGnssMeasurementsCallback(gnssCallback)
        sensorManager.unregisterListener(this)
    }

    @SuppressLint("MissingPermission")
    fun snapshot(deviceId: String): JSONObject {
        val now = System.currentTimeMillis()
        if (now - lastWifiScanMs > 30_000) {
            runCatching { wifiManager.startScan() }
            lastWifiScanMs = now
        }
        return JSONObject().apply {
            put("device_id", deviceId)
            put("timestamp_ms", now)
            put("location", location?.let { locationJson(it) } ?: JSONObject.NULL)
            put("imu", JSONObject().apply {
                put("accel_enu_mps2", JSONArray(accelEnu.toList()))
                put("gyro_rps", JSONArray(gyro.toList()))
                pressureHpa?.let { put("pressure_hpa", it) }
            })
            put("wifi", wifiJson())
            put("cells", cellJson())
            put("gnss_clock", gnssClock ?: JSONObject.NULL)
            put("gnss_raw", rawGnss)
        }
    }

    override fun onLocationChanged(value: Location) { location = value }
    override fun onProviderEnabled(provider: String) = Unit
    override fun onProviderDisabled(provider: String) = Unit
    override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) = Unit

    override fun onSensorChanged(event: SensorEvent) {
        when (event.sensor.type) {
            Sensor.TYPE_ROTATION_VECTOR -> {
                val m = FloatArray(9)
                SensorManager.getRotationMatrixFromVector(m, event.values)
                rotation = m
            }
            Sensor.TYPE_LINEAR_ACCELERATION -> {
                val v = event.values
                val r = rotation
                accelEnu = floatArrayOf(
                    r[0]*v[0] + r[1]*v[1] + r[2]*v[2],
                    r[3]*v[0] + r[4]*v[1] + r[5]*v[2],
                    r[6]*v[0] + r[7]*v[1] + r[8]*v[2]
                )
            }
            Sensor.TYPE_GYROSCOPE -> gyro = event.values.clone()
            Sensor.TYPE_PRESSURE -> pressureHpa = event.values[0]
        }
    }
    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) = Unit

    private fun locationJson(l: Location) = JSONObject().apply {
        put("latitude_deg", l.latitude); put("longitude_deg", l.longitude); put("accuracy_m", l.accuracy.toDouble()); put("provider", l.provider)
        if (l.hasAltitude()) put("altitude_m", l.altitude)
        if (l.hasSpeed()) put("speed_mps", l.speed.toDouble())
        if (l.hasBearing()) put("bearing_deg", l.bearing.toDouble())
    }

    private fun wifiJson(): JSONArray {
        val arr = JSONArray()
        runCatching { wifiManager.scanResults }.getOrDefault(emptyList()).take(64).forEach { ap ->
            arr.put(JSONObject().apply { put("bssid", ap.BSSID); put("rssi_dbm", ap.level); put("frequency_mhz", ap.frequency) })
        }
        return arr
    }

    @SuppressLint("MissingPermission")
    private fun cellJson(): JSONArray {
        val arr = JSONArray()
        val cells = runCatching { telephonyManager.allCellInfo }.getOrNull() ?: return arr
        cells.take(32).forEach { info ->
            cellRecord(info)?.let { arr.put(it) }
        }
        return arr
    }

    private fun cellRecord(info: CellInfo): JSONObject? = when (info) {
        is CellInfoLte -> JSONObject().apply {
            val id=info.cellIdentity; val sig=info.cellSignalStrength
            put("key", "lte:${id.mccString}:${id.mncString}:${id.tac}:${id.ci}"); put("technology","LTE"); put("signal_dbm",sig.dbm); put("registered",info.isRegistered)
        }
        is CellInfoNr -> JSONObject().apply {
            val id=info.cellIdentity as CellIdentityNr; val sig=info.cellSignalStrength as CellSignalStrengthNr
            put("key", "nr:${id.mccString}:${id.mncString}:${id.tac}:${id.nci}"); put("technology","NR"); put("signal_dbm",sig.dbm); put("registered",info.isRegistered)
        }
        is CellInfoWcdma -> JSONObject().apply {
            val id=info.cellIdentity; val sig=info.cellSignalStrength
            put("key", "wcdma:${id.mccString}:${id.mncString}:${id.lac}:${id.cid}"); put("technology","WCDMA"); put("signal_dbm",sig.dbm); put("registered",info.isRegistered)
        }
        is CellInfoGsm -> JSONObject().apply {
            val id=info.cellIdentity; val sig=info.cellSignalStrength
            put("key", "gsm:${id.mccString}:${id.mncString}:${id.lac}:${id.cid}"); put("technology","GSM"); put("signal_dbm",sig.dbm); put("registered",info.isRegistered)
        }
        else -> null
    }

    private fun measurementJson(m: GnssMeasurement) = JSONObject().apply {
        put("svid", m.svid); put("constellation_type", m.constellationType); put("cn0_dbhz", m.cn0DbHz); put("pseudorange_rate_mps", m.pseudorangeRateMetersPerSecond); put("state", m.state)
        put("accumulated_delta_range_state", m.accumulatedDeltaRangeState)
        if ((m.accumulatedDeltaRangeState and GnssMeasurement.ADR_STATE_VALID) != 0) put("accumulated_delta_range_m", m.accumulatedDeltaRangeMeters)
        if (m.hasCarrierFrequencyHz()) put("carrier_frequency_hz", m.carrierFrequencyHz.toDouble())
    }
}

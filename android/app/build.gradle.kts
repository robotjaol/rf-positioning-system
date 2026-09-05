plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "org.robotjaol.resilientpositioning"
    compileSdk = 37

    defaultConfig {
        applicationId = "org.robotjaol.resilientpositioning"
        minSdk = 29
        targetSdk = 37
        versionCode = 1
        versionName = "0.1.0"
    }
}

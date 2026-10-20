pragma Singleton
import QtQuick
import Quickshell
import "Locale.js" as Locale
import "Catalogs.js" as Catalogs

QtObject {
    id: translations
    property var environment: ({LC_ALL: Quickshell.env("LC_ALL"), LC_MESSAGES: Quickshell.env("LC_MESSAGES"), LANG: Quickshell.env("LANG")})
    readonly property string systemLocale: Locale.systemLocale(environment)
    readonly property var supported: Catalogs.languages
    readonly property string locale: Locale.select(systemLocale, supported)
    readonly property string languageName: supported[locale].nativeName
    readonly property var regional: Catalogs.qml[locale] || ({})
    readonly property var base: Catalogs.qml[locale.split("_")[0]] || ({})

    function tr(source, values = []) {
        return Locale.translate(source, regional, base, values);
    }
}

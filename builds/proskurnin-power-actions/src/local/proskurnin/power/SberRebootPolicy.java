package local.proskurnin.power;

/** Sber-only candidate. Must be hardware-tested before installing as the active helper. */
final class SberRebootPolicy {
    static String reason(String model, String device, String fingerprint) {
        if (!"SaluteTV".equals(model) || !"m7332_eu".equals(device)
                || !"MediaTek/m7332_eu/m7332_eu:9/PPR2.180905.006.A1/yankeqi12211211:userdebug/release-keys".equals(fingerprint)) {
            throw new SecurityException("Unverified power profile");
        }
        // Native bootloader handles boot-poweron and selects one-time direct startup.
        return "poweron";
    }
}

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


DETECTOR = Path(__file__).resolve().parents[1] / "hardware/detect.sh"
ASSOCIATIVE_ARRAYS = subprocess.run(["bash", "-c", "declare -A probe=()"],
                                    capture_output=True).returncode == 0


@unittest.skipUnless(ASSOCIATIVE_ARRAYS, "detect.sh requires bash 4+ (Arch ships bash 5)")
class HardwareDetectionTests(unittest.TestCase):
    def run_detector(self, cpu, vendors, nvidia_driver=None, kernels=("linux",), supplies=None, chassis="3"):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            modules = root / "modules"
            for index, kernel in enumerate(kernels):
                (modules / f"6.{index}.0").mkdir(parents=True)
                (modules / f"6.{index}.0/pkgbase").write_text(kernel + "\n")
            cpuinfo = root / "cpuinfo"
            cpuinfo.write_text(f"vendor_id\t: {cpu}\n")
            pci = root / "pci"
            pci.mkdir()
            for index, vendor in enumerate(vendors):
                device = pci / str(index)
                device.mkdir()
                (device / "class").write_text("0x030000\n")
                (device / "vendor").write_text(vendor + "\n")
            power = root / "power_supply"
            power.mkdir()
            for name, kind in (supplies or {}).items():
                (power / name).mkdir()
                (power / name / "type").write_text(kind + "\n")
            (root / "chassis_type").write_text(chassis + "\n")
            env = os.environ.copy()
            env.update(HARDWARE_SYSFS_ROOT=str(pci), HARDWARE_CPUINFO=str(cpuinfo),
                       HARDWARE_MODULES_ROOT=str(modules), HARDWARE_POWER_SUPPLY_ROOT=str(power),
                       HARDWARE_CHASSIS_TYPE=str(root / "chassis_type"))
            env.pop("DISTRO_NVIDIA_DRIVER", None)
            if nvidia_driver:
                env["DISTRO_NVIDIA_DRIVER"] = nvidia_driver
            return subprocess.run(["bash", str(DETECTOR)], env=env,
                                  capture_output=True, text=True, check=False)

    def test_amd_cpu_and_gpu(self):
        result = self.run_detector("AuthenticAMD", ["0x1002"])
        self.assertEqual(result.returncode, 0, result.stderr)
        packages = set(result.stdout.splitlines())
        self.assertTrue({"amd-ucode", "mesa", "lib32-mesa", "vulkan-radeon",
                         "lib32-vulkan-radeon", "lib32-vulkan-icd-loader"} <= packages)
        self.assertNotIn("intel-ucode", packages)

    def test_intel_cpu_and_gpu(self):
        result = self.run_detector("GenuineIntel", ["0x8086"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue({"intel-ucode", "vulkan-intel", "lib32-vulkan-intel"} <=
                        set(result.stdout.splitlines()))

    def test_nvidia_requires_explicit_generation_choice(self):
        result = self.run_detector("GenuineIntel", ["0x8086", "0x10de"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DISTRO_NVIDIA_DRIVER=open", result.stderr)
        selected = self.run_detector("GenuineIntel", ["0x8086", "0x10de"], "open")
        self.assertEqual(selected.returncode, 0, selected.stderr)
        self.assertTrue({"nvidia-open", "lib32-nvidia-utils", "nvidia-settings",
                         "nvidia-prime", "vulkan-intel"} <= set(selected.stdout.splitlines()))

    def test_nvidia_uses_dkms_with_a_non_default_kernel(self):
        result = self.run_detector("AuthenticAMD", ["0x10de"], "open", kernels=("linux", "linux-lts"))
        self.assertEqual(result.returncode, 0, result.stderr)
        packages = result.stdout.splitlines()
        self.assertIn("nvidia-open-dkms", packages)
        self.assertNotIn("nvidia-open", packages)
        self.assertTrue({"linux-headers", "linux-lts-headers"} <= set(packages))
        self.assertEqual(len(packages), len(set(packages)))
        default = self.run_detector("AuthenticAMD", ["0x10de"], "open").stdout.splitlines()
        self.assertIn("nvidia-open", default)
        self.assertFalse([package for package in default if package.endswith("-headers")])

    def test_virtual_gpu_gets_software_vulkan(self):
        result = self.run_detector("GenuineIntel", ["0x1af4"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("lib32-vulkan-swrast", result.stdout.splitlines())

    def test_two_mesa_gpus_do_not_duplicate_packages(self):
        result = self.run_detector("AuthenticAMD", ["0x1002", "0x8086"])
        self.assertEqual(result.returncode, 0, result.stderr)
        packages = result.stdout.splitlines()
        self.assertEqual(len(packages), len(set(packages)))
        self.assertIn("vulkan-radeon", packages)
        self.assertIn("vulkan-intel", packages)

    def test_power_profiles_only_on_laptops(self):
        desktop = self.run_detector("AuthenticAMD", ["0x1002"], supplies={"AC": "Mains", "hidpp_battery_0": "Battery"})
        self.assertEqual(desktop.returncode, 0, desktop.stderr)
        self.assertNotIn("power-profiles-daemon", desktop.stdout.splitlines())
        battery = self.run_detector("AuthenticAMD", ["0x1002"], supplies={"BAT0": "Battery"})
        self.assertIn("power-profiles-daemon", battery.stdout.splitlines())
        self.assertIn("Laptop detected", battery.stderr)
        convertible = self.run_detector("GenuineIntel", ["0x8086"], chassis="31")
        self.assertIn("power-profiles-daemon", convertible.stdout.splitlines())

    def test_laptops_get_audio_firmware_and_intel_laptops_thermald(self):
        intel_laptop = self.run_detector("GenuineIntel", ["0x8086"], supplies={"BAT0": "Battery"}).stdout.splitlines()
        self.assertIn("sof-firmware", intel_laptop)
        self.assertIn("thermald", intel_laptop)
        amd_laptop = self.run_detector("AuthenticAMD", ["0x1002"], supplies={"BAT1": "Battery"}).stdout.splitlines()
        self.assertIn("sof-firmware", amd_laptop)
        self.assertNotIn("thermald", amd_laptop)
        intel_desktop = self.run_detector("GenuineIntel", ["0x8086"]).stdout.splitlines()
        self.assertNotIn("sof-firmware", intel_desktop)
        self.assertNotIn("thermald", intel_desktop)

    def test_unknown_gpu_stops_install(self):
        result = self.run_detector("GenuineIntel", ["0xffff"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No supported GPU", result.stderr)


if __name__ == "__main__":
    unittest.main()

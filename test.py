from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Konfigurasi Chrome WebDriver untuk CI/CD di GitHub Actions
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # Mode headless (tanpa UI)
chrome_options.add_argument("--no-sandbox")  # Dibutuhkan agar berjalan di GitHub Actions
chrome_options.add_argument("--disable-dev-shm-usage")  # Mencegah masalah shared memory di Linux
chrome_options.add_argument("--disable-gpu")  # Tidak perlu GPU di server CI/CD

# Set up WebDriver dengan konfigurasi yang sudah diperbaiki
driver = webdriver.Chrome(options=chrome_options)

# Base URL untuk sistem yang diuji
BASE_URL = "http://127.0.0.1:8000/"

# List untuk menyimpan hasil test
test_results = []

def run_test(test_function):
    """
    Helper function untuk menjalankan setiap test case tanpa menghentikan eksekusi.
    Jika ada error, akan dicatat dan test berikutnya tetap dijalankan.
    """
    try:
        test_function()
        test_results.append((test_function.__name__, "✅ PASSED", ""))
    except AssertionError as e:
        test_results.append((test_function.__name__, "❌ FAILED", str(e)))
    except Exception as e:
        test_results.append((test_function.__name__, "⚠️ ERROR", str(e)))

def test_login_valid():
    driver.get(BASE_URL + "login.php")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "username"))).send_keys("testuser")
    driver.find_element(By.ID, "InputPassword").send_keys("Test@123")
    driver.find_element(By.NAME, "submit").click()

    time.sleep(2)
    assert "Not Found" not in driver.page_source, "Error: index.php tidak ditemukan setelah login."

def test_login_invalid():
    driver.get(BASE_URL + "login.php")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "username"))).send_keys("wronguser")
    driver.find_element(By.ID, "InputPassword").send_keys("WrongPass")
    driver.find_element(By.NAME, "submit").click()

    time.sleep(2)
    assert "Register User Gagal" in driver.page_source, "Error: Pesan gagal login tidak muncul."

def test_login_empty():
    driver.get(BASE_URL + "login.php")
    driver.find_element(By.NAME, "submit").click()

    time.sleep(2)
    assert "Data tidak boleh kosong" in driver.page_source, "Error: Input kosong tidak ditangani dengan benar."

def test_register_valid():
    driver.get(BASE_URL + "register.php")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "username"))).send_keys("newuser")
    driver.find_element(By.ID, "name").send_keys("New User")
    driver.find_element(By.ID, "InputEmail").send_keys("newuser@example.com")
    driver.find_element(By.ID, "InputPassword").send_keys("Test@123")
    driver.find_element(By.ID, "InputRePassword").send_keys("Test@123")
    driver.find_element(By.NAME, "submit").click()

    time.sleep(2)
    assert "Not Found" not in driver.page_source, "Error: index.php tidak ditemukan setelah registrasi."

def test_register_existing_user():
    driver.get(BASE_URL + "register.php")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "username"))).send_keys("existinguser")
    driver.find_element(By.ID, "name").send_keys("Existing User")
    driver.find_element(By.ID, "InputEmail").send_keys("existing@example.com")
    driver.find_element(By.ID, "InputPassword").send_keys("Test@123")
    driver.find_element(By.ID, "InputRePassword").send_keys("Test@123")
    driver.find_element(By.NAME, "submit").click()

    time.sleep(2)
    assert "Username sudah terdaftar" in driver.page_source, "Error: Sistem tidak mendeteksi username yang sudah ada."

def test_register_password_mismatch():
    driver.get(BASE_URL + "register.php")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "username"))).send_keys("anotheruser")
    driver.find_element(By.ID, "name").send_keys("Another User")
    driver.find_element(By.ID, "InputEmail").send_keys("another@example.com")
    driver.find_element(By.ID, "InputPassword").send_keys("Test@123")
    driver.find_element(By.ID, "InputRePassword").send_keys("WrongPass")
    driver.find_element(By.NAME, "submit").click()

    time.sleep(2)
    assert "Password tidak sama" in driver.page_source, "Error: Sistem tidak menangani password yang tidak cocok dengan benar."

def test_sql_injection_login():
    driver.get(BASE_URL + "login.php")

    # Pastikan elemen ditemukan sebelum mengisi
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "username"))).send_keys("' OR '1'='1")
    driver.find_element(By.ID, "InputPassword").send_keys("' OR '1'='1")
    driver.find_element(By.NAME, "submit").click()

    time.sleep(2)
    assert "Not Found" not in driver.page_source, "Error: SQL Injection berhasil, sistem tidak aman!"

def test_sql_injection_register():
    driver.get(BASE_URL + "register.php")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "username"))).send_keys("' OR '1'='1")
    driver.find_element(By.ID, "name").send_keys("' OR '1'='1")
    driver.find_element(By.ID, "InputEmail").send_keys("hacker@example.com")
    driver.find_element(By.ID, "InputPassword").send_keys("' OR '1'='1")
    driver.find_element(By.ID, "InputRePassword").send_keys("' OR '1'='1")
    driver.find_element(By.NAME, "submit").click()

    time.sleep(2)
    assert "Not Found" in driver.page_source, "Error: SQL Injection berhasil masuk ke database!"

# Jalankan semua test case menggunakan run_test()
test_cases = [
    test_login_valid,
    test_login_invalid,
    test_login_empty,
    test_register_valid,
    test_register_existing_user,
    test_register_password_mismatch,
    test_sql_injection_login,
    test_sql_injection_register
]

for test in test_cases:
    run_test(test)

# Cetak hasil semua test dengan format rapi
print("\n=== TEST RESULTS ===")
print(f"{'Test Case':<30} {'Status':<10} {'Message'}")
print("="*80)
for name, status, message in test_results:
    print(f"{name:<30} {status:<10} {message}")

# Tutup browser
driver.quit()

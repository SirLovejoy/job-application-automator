# automated_job_applier.py
# Python + Selenium script to help fill job applications (including LinkedIn Easy Apply)
# WARNING: Automating job applications may violate terms of service of some platforms.
#          Use responsibly, at low volume, and for personal/educational purposes only.

import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

def load_personal_info(file_path='personal_info.json'):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'resume_path' in data and data['resume_path'].startswith('~/'):
            import os
            data['resume_path'] = os.path.expanduser(data['resume_path'])
        return data
    except FileNotFoundError:
        template = {
            "first_name": "First",
            "last_name": "Last",
            "full_name": "First Last",
            "email": "your.email@example.com",
            "phone": "+1 123-456-7890",
            "linkedin": "https://www.linkedin.com/in/yourprofile",
            "resume_path": "C:/Users/You/Documents/resume.pdf",  # ← change to absolute path
            # Add answers to common screening questions
            "years_experience": "5",
            "current_company": "Current Corp",
            "willing_to_relocate": "Yes",
            # etc.
        }
        with open(file_path.replace('.json', '.json.example'), 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=4)
        print("Created personal_info.json.example — please copy it to personal_info.json and edit.")
        exit(1)


def fill_form_fields(driver, wait, field_mappings, personal_info):
    for key, selector_info in field_mappings.items():
        if key not in personal_info or not personal_info[key]:
            continue
        value = str(personal_info[key])
        by, selector = selector_info if isinstance(selector_info, tuple) else (By.CSS_SELECTOR, selector_info)

        try:
            elem = wait.until(EC.presence_of_element_located((by, selector)))
            if elem.tag_name in ['input', 'textarea']:
                if 'file' in elem.get_attribute('outerHTML'):
                    elem.send_keys(value)
                    time.sleep(1.2)
                elif elem.get_attribute('value') in ['', ' ']:
                    elem.clear()
                    elem.send_keys(value)
                    time.sleep(0.5)
            elif elem.tag_name == 'select':
                from selenium.webdriver.support.ui import Select
                Select(elem).select_by_visible_text(value)
            print(f"✓ Filled: {key}")
        except (TimeoutException, NoSuchElementException):
            print(f"→ Not found: {key}")
        except Exception as e:
            print(f"Error filling {key}: {e}")


def apply_linkedin_easy_apply(job_url, personal_info, auto_submit=False):
    options = Options()
    # options.add_argument("--headless")  # uncomment to hide browser
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)

    try:
        print(f"Opening: {job_url}")
        driver.get(job_url)
        time.sleep(3 + random.uniform(0, 2))

        # Click Easy Apply if visible
        try:
            btn = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.jobs-apply-button, button[aria-label*='Easy Apply']")
            ))
            btn.click()
            time.sleep(3)
        except:
            print("No Easy Apply button found or already in form.")

        # Common LinkedIn field selectors (many are pre-filled)
        mappings = {
            "phone":               (By.CSS_SELECTOR, "input[aria-label*='phone number'], input[id*='phone']"),
            "resume_path":         (By.CSS_SELECTOR, "input[type='file'][aria-label*='resume'], input[name*='file']"),
            "years_experience":    (By.CSS_SELECTOR, "input[aria-label*='years'], input[placeholder*='years']"),
            # Add more when you see them
        }

        fill_form_fields(driver, wait, mappings, personal_info)

        # Handle common Yes/No questions (very basic – improve as needed)
        try:
            for label in driver.find_elements(By.CSS_SELECTOR, "label"):
                txt = label.text.lower()
                if "sponsorship" in txt or "require sponsorship" in txt:
                    if personal_info.get("require_sponsorship", "No").lower() == "no":
                        label.click()
                elif "relocate" in txt:
                    if personal_info.get("willing_to_relocate", "Yes").lower() == "yes":
                        label.click()
        except:
            pass

        # Click through steps
        max_steps = 7
        for _ in range(max_steps):
            for text, sel in [
                ("Next", "button[aria-label*='Continue'], button.jobs-easy-apply-next-button"),
                ("Review", "button[aria-label*='Review']"),
                ("Submit application", "button[aria-label*='Submit'], button.jobs-easy-apply-submit-button")
            ]:
                try:
                    btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                    print(f"→ Clicking: {text}")
                    if auto_submit and "submit" in text.lower():
                        btn.click()
                        time.sleep(4)
                        print("Submitted (check manually if successful)")
                        return
                    else:
                        btn.click()
                        time.sleep(2.5 + random.uniform(0, 1.5))
                    break
                except:
                    continue
            else:
                print("No more Next/Submit buttons found.")
                break

        print("Finished attempting application. Check browser or LinkedIn.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if not auto_submit:
            input("\nPress Enter to close browser...")
        driver.quit()


if __name__ == "__main__":
    info = load_personal_info()

    # ← Paste a real LinkedIn job URL here
    example_url = "https://www.linkedin.com/jobs/view/1234567890123456789/"

    apply_linkedin_easy_apply(
        example_url,
        info,
        auto_submit=False     # ← Change to True ONLY after testing thoroughly
    )
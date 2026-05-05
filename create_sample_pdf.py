"""
NyayaSetu — Sample Judgment Generator
Creates a realistic sample court judgment PDF for demo purposes.
Run: python create_sample_pdf.py
"""
import sys
from pathlib import Path

def create_sample_pdf():
    try:
        import fitz
    except ImportError:
        print("ERROR: pymupdf not installed. Run: pip install pymupdf")
        sys.exit(1)

    judgment_text = """
IN THE HIGH COURT OF JUDICATURE AT BOMBAY
ORDINARY ORIGINAL CIVIL JURISDICTION

WRIT PETITION NO. 4521 OF 2024

IN THE MATTER OF:
RAJESH KUMAR SHARMA                                             ...PETITIONER

VERSUS

STATE OF MAHARASHTRA & ORS.                                   ...RESPONDENTS

CORAM: HON'BLE MR. JUSTICE PRAKASH NARAYANAN
       HON'BLE MRS. JUSTICE SUNITA MEHTA

DATE OF ORDER: 15th March, 2024

─────────────────────────────────────────────────────────────────────────────

JUDGMENT

1. The petitioner, Rajesh Kumar Sharma, has filed this writ petition under Article 226 of the Constitution of India challenging the arbitrary termination of his services from the Public Works Department, Government of Maharashtra, without following due process of law and in violation of the principles of natural justice.

2. The petitioner was appointed as a Junior Engineer in the Public Works Department (PWD) of the Government of Maharashtra on 15th January 2019. By an order dated 10th September 2023, his services were terminated without any prior notice, inquiry, or opportunity to be heard, citing "administrative reorganisation."

3. The Respondent No. 1 (State of Maharashtra) and Respondent No. 2 (Department of Public Works) appeared through their learned counsel and contended that the termination was in accordance with the service rules and was purely administrative in nature.

4. FINDINGS OF THE COURT:

After carefully perusing the pleadings and hearing the arguments of the learned counsel for both parties, this Court finds that:

(a) The termination of the petitioner's services without conducting a departmental inquiry and without affording him a reasonable opportunity to be heard is manifestly in violation of the principles of natural justice.

(b) The impugned order dated 10th September 2023 is arbitrary, illegal, and violative of Article 14 and Article 21 of the Constitution of India.

(c) The respondents have failed to demonstrate any valid justification for bypassing the mandatory procedural safeguards.

5. DIRECTIONS:

In view of the aforesaid findings, this Court hereby issues the following directions:

(i) The impugned termination order dated 10th September, 2023 is hereby quashed and set aside.

(ii) Respondent No. 1 — State of Maharashtra, through its Principal Secretary, Department of Public Works — is directed to reinstate the petitioner to his original post of Junior Engineer within a period of FOUR WEEKS from the date of this order.

(iii) The petitioner shall be entitled to all consequential service benefits including continuity of service, but shall NOT be entitled to back wages for the period of termination, considering that he was gainfully employed elsewhere during this period.

(iv) Respondent No. 2 is further directed to conduct a fresh departmental inquiry, if it so desires, in accordance with law and only after reinstating the petitioner, within a period of THREE MONTHS from the date of reinstatement.

(v) The respondents are directed to pay costs of Rs. 25,000/- to the petitioner within six weeks from today.

6. APPEAL / LIMITATION:

Any appeal against this judgment shall lie before the Division Bench of this Court. The limitation period for filing a Letters Patent Appeal is 30 days from the date of this order, i.e., the last date for appeal is 14th April, 2024.

7. Accordingly, the Writ Petition is ALLOWED in the above terms.

                                               (JUSTICE PRAKASH NARAYANAN)

                                               (JUSTICE SUNITA MEHTA)

MUMBAI
DATE: 15th MARCH, 2024
"""

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    # Write text
    fontsize = 10
    x, y = 50, 50
    line_height = 14

    lines = judgment_text.strip().split('\n')
    for line in lines:
        if y > 800:
            page = doc.new_page(width=595, height=842)
            y = 50
        # Determine font size
        fs = fontsize
        if 'HIGH COURT' in line or 'JUDGMENT' == line.strip():
            fs = 12
        elif line.strip().startswith('IN THE MATTER') or 'CORAM:' in line:
            fs = 10
        page.insert_text((x, y), line, fontsize=fs, color=(0, 0, 0))
        y += line_height

    output = Path("sample_judgments/sample_judgment_WP4521_2024.pdf")
    output.parent.mkdir(exist_ok=True)
    doc.save(str(output))
    doc.close()
    print(f"[OK] Sample judgment created: {output}")


if __name__ == "__main__":
    create_sample_pdf()

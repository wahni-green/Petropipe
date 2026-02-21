import frappe
from frappe.exceptions import DuplicateEntryError

def auto_job_card(doc, method=None):
    if not doc.job_no:
        return
    
    job_card_name = frappe.db.exists("Job Card Master",{"job_no": doc.job_no})
    if job_card_name:
        try:
            frappe.db.set_value("Job Card Master", job_card_name, {
                "customer": doc.customer or '',
                "incoterm": doc.incoterm or '',
                "sales_order": doc.name or '',
                "company": doc.company or '',
                "grand_total": doc.grand_total or '',
            }, update_modified=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Job Card Master Update Failed")
    else:
        try:
            job_card_master = frappe.new_doc("Job Card Master")
            job_card_master.sales_order = doc.name
            job_card_master.job_no = doc.job_no
            job_card_master.customer = doc.customer or ""
            job_card_master.incoterm = doc.incoterm or ""
            job_card_master.company = doc.company or ""
            job_card_master.grand_total = doc.grand_total or 0
            job_card_master.insert(ignore_permissions=True)
        except DuplicateEntryError:
            existing_name = frappe.db.get_value( "Job Card Master",{"job_no": doc.job_no},"name")
            if existing_name:
                frappe.db.set_value("Job Card Master", existing_name, {
                    "customer": doc.customer or "",
                    "incoterm": doc.incoterm or "",
                    "sales_order": doc.name or "",
                    "company": doc.company or "",
                    "grand_total": doc.grand_total or ""
                }, update_modified=True)

        except Exception:
            frappe.log_error(frappe.get_traceback(),"Job Card Master Creation Failed")
             
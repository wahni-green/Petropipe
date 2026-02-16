import frappe

def auto_job_card(doc, method=None):
    if not doc.job_no:
        return
    
    job_card_name = frappe.db.get_value("Job Card Master", {"job_no": doc.job_no}, "name")
    if job_card_name:
        frappe.db.set_value("Job Card Master", job_card_name, {
            "customer": doc.customer or '',
            "incoterm": doc.incoterm or '',
            "sales_order": doc.name or '',
            "company": doc.company or ''
        }, update_modified=True)
    else:
        try:
            job_card_master = frappe.new_doc("Job Card Master")
            job_card_master.sales_order = doc.name
            job_card_master.job_no = doc.job_no
            job_card_master.customer = doc.customer or ''
            job_card_master.incoterm = doc.incoterm or ''
            job_card_master.company = doc.company or ''
            job_card_master.insert(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Job Card Master Creation Failed")
            
// Copyright (c) 2024, Wahni IT Solutions and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Event Insight"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "lead",
			label: __("Lead"),
			fieldtype: "Link",
			options: "Lead",
			reqd: 0
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "period",
			label: __("Period"),
			fieldtype: "Select",
			options: ["Weekly", "Monthly", "Quarterly", "Half-Yearly", "Yearly"],
			default: "Monthly",
		},
	]
};

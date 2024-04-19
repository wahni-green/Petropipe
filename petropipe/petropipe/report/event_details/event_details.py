# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder.functions import Count, Sum
from frappe import _, scrub
from frappe.utils import add_days, add_to_date, flt, getdate

from erpnext.accounts.utils import get_fiscal_year
# from erpnext.crm.report.campaign_efficiency.campaign_efficiency import get_lead_data


def execute(filters=None):

	filters = frappe._dict(filters or {})
	months = [
			"Jan",
			"Feb",
			"Mar",
			"Apr",
			"May",
			"Jun",
			"Jul",
			"Aug",
			"Sep",
			"Oct",
			"Nov",
			"Dec",
		]
	period_range = get_period_date_ranges(filters)
	columns, data = get_columns(filters, period_range, months), get_data(filters)
	return columns, data


def get_data(filters=None):
	
	result = {}
	event = frappe.qb.DocType("Event")
	ep = frappe.qb.DocType("Event Participants")

	query = (
		frappe.qb.from_(event)
		.left_join(ep).on(ep.parent == event.name)

		.select(
			event.name.as_('event'),
			event.subject, event.starts_on,
			event.event_type, event.event_category, event.status,
			ep.reference_docname.as_('lead'), ep.reference_doctype,
			Count(event.event_category).as_("count"),
		)
		.where(event.status == "Open")
		.where(ep.reference_doctype == "Lead")
		.groupby(ep.reference_docname,event.event_category)
	)
	if filters.get("lead"):
		query = query.where(ep.reference_docname == filters.get("lead"))
	# if filters.get("period") == "Monthly":
	# 	query = query.where(task.name == filters.get("task"))

	data = query.run(as_dict=1)
	lead = set(d.get('lead') for d in data)
	leads = list(lead)

	for d in data:
		result.setdefault(d.get('lead') , {})
		result[d.get('lead')][d.get('event_category')] = d.get('count')
		result[d.get('lead')]['quotations'] = get_lead_quotation_count(leads)
		result[d.get('lead')]['opportunity'] = get_lead_opp_count(leads)

	row = []
	for key, val in result.items():

		row.append({
			'lead': key,
			'introduction_email': val.get('Introduction Email'),
			'followup_email': val.get('Follow-Up Email'),
			'meeting': val.get('Meeting'),
			'quotations': val.get('quotations'),
			'opportunity': val.get('opportunity')
		})

	return row

def get_period_date_ranges(filters):
		from dateutil.relativedelta import MO, relativedelta

		from_date, to_date = getdate(filters.from_date), getdate(filters.to_date)

		increment = {"Monthly": 1, "Quarterly": 3, "Half-Yearly": 6, "Yearly": 12}.get(filters.period, 1)

		if filters.period in ["Monthly", "Quarterly"]:
			from_date = from_date.replace(day=1)
		elif filters.range == "Yearly":
			from_date = get_fiscal_year(from_date)[1]
		else:
			from_date = from_date + relativedelta(from_date, weekday=MO(-1))

		periodic_daterange = []
		for _dummy in range(1, 53):
			if filters.period == "Weekly":
				period_end_date = add_days(from_date, 6)
			else:
				period_end_date = add_to_date(from_date, months=increment, days=-1)

			if period_end_date > to_date:
				period_end_date = to_date

			periodic_daterange.append(period_end_date)

			from_date = add_days(period_end_date, 1)

			if period_end_date == to_date:
				break
		return periodic_daterange

def get_lead_quotation_count(leads):
	return frappe.db.sql(
		"""select count(name) from `tabQuotation`
		where quotation_to = 'Lead' and party_name in (%s)"""
		% ", ".join(["%s"] * len(leads)),
		tuple(leads),
	)[0][0]  # nosec

def get_lead_opp_count(leads):
	return frappe.db.sql(
		"""select count(name) from `tabOpportunity`
	where opportunity_from = 'Lead' and party_name in (%s)"""
		% ", ".join(["%s"] * len(leads)),
		tuple(leads),
	)[0][0]

def get_period(posting_date, filters, months):
		if filters.period == "Weekly":
			period = _("Week {0} {1}").format(str(posting_date.isocalendar()[1]), str(posting_date.year))
		elif filters.period == "Monthly":
			period = _(str(months[posting_date.month - 1])) + " " + str(posting_date.year)
		elif filters.period == "Quarterly":
			period = _("Quarter {0} {1}").format(
				str(((posting_date.month - 1) // 3) + 1), str(posting_date.year)
			)
		else:
			year = get_fiscal_year(posting_date, company=filters.company)
			period = str(year[0])
		return period

def get_columns(filters=None, period_range=None, months=None):
	columns = [
		{
			"label": _("Lead"),
			"fieldname": "lead",
			"fieldtype": "Link",
			"options": "Lead",
			"width": 200
		},
		{
			"label": _("No of Introduction Email"),
			"fieldname": "introduction_email",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("No of Follow-Up Email"),
			"fieldname": "followup_email",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("No of Meetings"),
			"fieldname": "meeting",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("No of Opportunity"),
			"fieldname": "opportunity",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("No of Quotations"),
			"fieldname": "quotations",
			"fieldtype": "Data",
			"width": 120
		},
	]
	labels = [
				_("No of Introduction Email"),
				_("No of Follow-Up Email"),
				_("No of Meetings"),
				_("No of Opportunity"),
				_("No of Quotations"),
			]
	for end_date in period_range:
			period = get_period(end_date, filters, months)
			for label in labels:
				columns.append(
					{"label": '{1}({0})'.format(frappe.unscrub(period),frappe.unscrub(label)), "fieldname": frappe.scrub("{0} {1}".format(label, period)), "fieldtype": "Float", "width": 120}
				)
	return columns


	
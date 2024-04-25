# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, add_to_date, getdate
from pypika.functions import Date

from erpnext.accounts.utils import get_fiscal_year


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
	columns, data = get_columns(filters, period_range, months), get_data(filters, months)
	return columns, data


def get_data(filters=None, months=None):
	lead = frappe.qb.DocType("Lead")
	query = (
		frappe.qb.from_(lead)
		.select(lead.name.as_("lead"), lead.lead_owner)
		.where(lead.lead_owner.notnull())
	)
	if filters.from_date:
		query = query.where(Date(lead.creation) >= filters.get("from_date"))
	if filters.to_date:
		query = query.where(Date(lead.creation) <= filters.get("to_date"))
	if filters.company:
		query = query.where(lead.company == filters.company)
	if filters.lead_owner:
		query = query.where(lead.lead_owner == filters.lead_owner)

	lead_details = query.run(as_dict=1)
	if not lead_details:
		return []
	lead_map = frappe._dict()
	for d in lead_details:
		lead_map.setdefault(d.get("lead_owner"), []).append(d.lead)

	# Getting all period date range 
	periodic_daterange = get_period_date_ranges(filters)

	labels = [
		"No of Introduction Email", "No of Follow-Up Email","No of Meetings",
		"No of Opportunity", "No of Quotations", "No of Lead"
	]

	data = []
	for lead_owner, leads in lead_map.items():
		row = {"lead_owner": lead_owner, }
		for label in labels:
			for end_date in periodic_daterange:
				period = get_period(end_date, filters, months)
				field_name = frappe.scrub("{0} {1}".format(label, period))

				if label == "No of Lead":
					row[field_name] = len(leads)
				elif label == "No of Introduction Email":
					row[field_name] = get_event_data(leads, lead_owner, filters, "Introduction Email", months).get(
					lead_owner, {}).get(period, 0
				)
				elif label == "No of Follow-Up Email":
					row[field_name] = get_event_data(leads, lead_owner, filters, "Follow-Up Email", months).get(
					lead_owner, {}).get(period, 0
				)
				elif label == "No of Meetings":
					row[field_name] = get_event_data(leads, lead_owner, filters, "Meeting", months).get(
					lead_owner, {}).get(period, 0
				)
				elif label == "No of Opportunity":
					row[field_name] = get_lead_opportunity_count(
						leads, lead_owner, filters, months
				).get(lead_owner, {}).get(period, 0)
				elif label == "No of Quotations":
					row[field_name] = get_lead_quotation_count(
						leads, lead_owner, filters, months
					).get(lead_owner, {}).get(period, 0)
		data.append(row)

	return data


def get_lead_quotation_count(leads, lead_owner, filters, months):
	quotation = frappe.qb.DocType("Quotation")
	quotation_data = (
		frappe.qb.from_(quotation)
		.select(
			quotation.party_name, quotation.name, quotation.transaction_date
		)
		.where(
			(quotation.quotation_to == "Lead")
			& (quotation.party_name.isin(leads))
		)
		.run(as_dict=1)
	)

	quotation_entries = {}
	for q_data in quotation_data:
		period = get_period(q_data.transaction_date, filters , months)
		quotation_entries.setdefault(lead_owner, frappe._dict()).setdefault(period, 0.0)
		quotation_entries[lead_owner][period] += 1

	return quotation_entries


def get_lead_opportunity_count(leads, lead_owner, filters, months):
	opportunity = frappe.qb.DocType("Opportunity")
	opportunity_data = (
		frappe.qb.from_(opportunity)
		.select(
			opportunity.party_name, opportunity.name, opportunity.creation
		)
		.where(
			(opportunity.opportunity_from == "Lead")
			& (opportunity.party_name.isin(leads))
		)
		.run(as_dict=1)
	)
	opportunity_enteries = {}
	for o_data in opportunity_data:
		period = get_period(getdate(o_data.creation), filters , months)
		opportunity_enteries.setdefault(lead_owner, frappe._dict()).setdefault(period, 0.0)
		opportunity_enteries[lead_owner][period] += 1		

	return opportunity_enteries


def get_event_data(leads, lead_owner, filters, type, months):
	event = frappe.qb.DocType("Event")
	event_p = frappe.qb.DocType("Event Participants")

	event_data = (
		frappe.qb.from_(event)
		.left_join(event_p).on(event_p.parent == event.name)
		.select(
			event_p.reference_docname.as_('lead'), event.event_category, event.starts_on
		)
		.where(
			(event.status == "Open") 
			& (event_p.reference_doctype == "Lead")
			& (event.event_category == type)
			& (event_p.reference_docname.isin(leads))
		)
		.run(as_dict=1)
	)
	event_entries = {}
	for e_data in event_data:
		period = get_period(getdate(e_data.starts_on), filters , months)
		event_entries.setdefault(lead_owner, frappe._dict()).setdefault(period, 0.0)
		event_entries[lead_owner][period] += 1

	return  event_entries


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


def get_columns(filters=None, period_range=None, months=None):
	columns = [
		{
			"label": _("Lead Owner"),
			"fieldname": "lead_owner",
			"fieldtype": "Link",
			"options": "User",
			"width": 200
		}
	]
	labels = [
		_("No of Lead"), _("No of Opportunity"), _("No of Quotations"),
		_("No of Introduction Email"), _("No of Follow-Up Email"), _("No of Meetings"),
	]

	for end_date in period_range:
			period = get_period(end_date, filters, months)
			for label in labels:
				columns.append(
					{
						"label": '{1}({0})'.format(frappe.unscrub(period),frappe.unscrub(label)), 
						"fieldname": frappe.scrub("{0} {1}".format(label, period)),
						"fieldtype": "Float", "width": 120
					}
				)
	return columns
# Copyright (c) 2023, Your Company
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from hrms.payroll.doctype.gratuity.gratuity import Gratuity


class CustomGratuity(Gratuity):
	def get_gratuity_amount(self, experience: float) -> float:
		"""Calculate gratuity based on UAE Labor Law:
		- 0-1 years: No gratuity
		- 1-5 years: 21 days per year
		- Above 5 years: 21 days for first 5 years + 30 days for each additional year
		"""
		years = experience
		total_component_amount = self.get_total_component_amount()
		if not total_component_amount:
			frappe.throw(_("Basic salary not found for employee {0}").format(self.employee))
		gratuity_amount = 0
		if years < 1:
			gratuity_amount = 0
		elif years <= 5:
			gratuity_amount = total_component_amount * years * 21 / 30
		else:
			first_five_years = total_component_amount * 5 * 21 / 30
			additional_years = total_component_amount * (years - 5) * 30 / 30
			gratuity_amount = first_five_years + additional_years
		return flt(gratuity_amount, self.precision("amount"))
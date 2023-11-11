# Copyright (c) 2023, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class DocumentLock(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		document: DF.DynamicLink
		document_type: DF.Link
		locked_by: DF.Link
		locked_on: DF.Datetime | None
	# end: auto-generated types
	pass

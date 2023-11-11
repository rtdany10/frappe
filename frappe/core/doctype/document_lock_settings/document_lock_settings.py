# Copyright (c) 2023, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class DocumentLockSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.core.doctype.document_lock_details.document_lock_details import DocumentLockDetails
		from frappe.types import DF

		allow_owners_to_unlock: DF.Check
		apply_on: DF.Literal["All DocType", "Selected DocType"]
		documents: DF.Table[DocumentLockDetails]
		enabled: DF.Check
		unlock_role: DF.Link | None
	# end: auto-generated types
	pass

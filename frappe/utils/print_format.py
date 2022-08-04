import os

from PyPDF2 import PdfWriter

import frappe
from frappe import _
from frappe.core.doctype.access_log.access_log import make_access_log
from frappe.desk.query_report import build_xlsx_data
from frappe.utils.pdf import get_pdf
from frappe.utils.csvutils import to_csv
from frappe.utils.xlsxutils import make_xlsx

no_cache = 1

base_template_path = "www/printview.html"
standard_format = "templates/print_formats/standard.html"

from frappe.www.printview import validate_print_permission


@frappe.whitelist()
def download_multi_pdf(doctype, name, format=None, no_letterhead=False, options=None):
	"""
	Concatenate multiple docs as PDF .

	Returns a PDF compiled by concatenating multiple documents. The documents
	can be from a single DocType or multiple DocTypes

	Note: The design may seem a little weird, but it exists exists to
	        ensure backward compatibility. The correct way to use this function is to
	        pass a dict to doctype as described below

	NEW FUNCTIONALITY
	=================
	Parameters:
	doctype (dict):
	        key (string): DocType name
	        value (list): of strings of doc names which need to be concatenated and printed
	name (string):
	        name of the pdf which is generated
	format:
	        Print Format to be used

	Returns:
	PDF: A PDF generated by the concatenation of the mentioned input docs

	OLD FUNCTIONALITY - soon to be deprecated
	=========================================
	Parameters:
	doctype (string):
	        name of the DocType to which the docs belong which need to be printed
	name (string or list):
	        If string the name of the doc which needs to be printed
	        If list the list of strings of doc names which needs to be printed
	format:
	        Print Format to be used

	Returns:
	PDF: A PDF generated by the concatenation of the mentioned input docs
	"""

	import json

	output = PdfWriter()

	if isinstance(options, str):
		options = json.loads(options)

	if not isinstance(doctype, dict):
		result = json.loads(name)

		# Concatenating pdf files
		for i, ss in enumerate(result):
			output = frappe.get_print(
				doctype,
				ss,
				format,
				as_pdf=True,
				output=output,
				no_letterhead=no_letterhead,
				pdf_options=options,
			)
		frappe.local.response.filename = "{doctype}.pdf".format(
			doctype=doctype.replace(" ", "-").replace("/", "-")
		)
	else:
		for doctype_name in doctype:
			for doc_name in doctype[doctype_name]:
				try:
					output = frappe.get_print(
						doctype_name,
						doc_name,
						format,
						as_pdf=True,
						output=output,
						no_letterhead=no_letterhead,
						pdf_options=options,
					)
				except Exception:
					frappe.log_error(
						title="Error in Multi PDF download",
						message=f"Permission Error on doc {doc_name} of doctype {doctype_name}",
						reference_doctype=doctype_name,
						reference_name=doc_name,
					)
		frappe.local.response.filename = f"{name}.pdf"

	frappe.local.response.filecontent = read_multi_pdf(output)
	frappe.local.response.type = "download"


def read_multi_pdf(output):
	# Get the content of the merged pdf files
	fname = os.path.join("/tmp", f"frappe-pdf-{frappe.generate_hash()}.pdf")
	output.write(open(fname, "wb"))

	with open(fname, "rb") as fileobj:
		filedata = fileobj.read()

	return filedata


@frappe.whitelist(allow_guest=True)
def download_pdf(doctype, name, format=None, doc=None, no_letterhead=0):
	doc = doc or frappe.get_doc(doctype, name)
	validate_print_permission(doc)

	html = frappe.get_print(doctype, name, format, doc=doc, no_letterhead=no_letterhead)
	frappe.local.response.filename = "{name}.pdf".format(
		name=name.replace(" ", "-").replace("/", "-")
	)
	frappe.local.response.filecontent = get_pdf(html)
	frappe.local.response.type = "pdf"


@frappe.whitelist()
def report_to_pdf(html, orientation="Landscape"):
	make_access_log(file_type="PDF", method="PDF", page=html)
	frappe.local.response.filename = "report.pdf"
	frappe.local.response.filecontent = get_pdf(html, {"orientation": orientation})
	frappe.local.response.type = "pdf"


@frappe.whitelist()
def print_by_server(
	doctype, name, printer_setting, print_format=None, doc=None, no_letterhead=0, file_path=None
):
	print_settings = frappe.get_doc("Network Printer Settings", printer_setting)
	try:
		import cups
	except ImportError:
		frappe.throw(_("You need to install pycups to use this feature!"))

	try:
		cups.setServer(print_settings.server_ip)
		cups.setPort(print_settings.port)
		conn = cups.Connection()
		output = PdfWriter()
		output = frappe.get_print(
			doctype, name, print_format, doc=doc, no_letterhead=no_letterhead, as_pdf=True, output=output
		)
		if not file_path:
			file_path = os.path.join("/", "tmp", f"frappe-pdf-{frappe.generate_hash()}.pdf")
		output.write(open(file_path, "wb"))
		conn.printFile(print_settings.printer_name, file_path, name, {})
	except OSError as e:
		if (
			"ContentNotFoundError" in e.message
			or "ContentOperationNotPermittedError" in e.message
			or "UnknownContentError" in e.message
			or "RemoteHostClosedError" in e.message
		):
			frappe.throw(_("PDF generation failed"))
	except cups.IPPError:
		frappe.throw(_("Printing failed"))


def get_report_content(filters, report, format="PDF"):
	"""Returns file in for the report in given format"""
	report = frappe.get_doc("Report", report)
	filters = frappe.parse_json(filters) if filters else {}

	columns, data = report.get_data(
		limit=100,
		user=frappe.session.user,
		filters=filters,
		as_dict=True,
		ignore_prepared_report=True,
	)

	# add serial numbers
	columns.insert(0, frappe._dict(fieldname="idx", label="", width="30px"))
	for i in range(len(data)):
		data[i]["idx"] = i + 1

	if len(data) == 0:
		frappe.throw(_("No data found."))

	if format == "PDF":
		columns = update_field_types(columns)
		html = get_html_table(report, columns, data)
		return get_pdf(html)

	elif format == "XLSX":
		report_data = frappe._dict()
		report_data["columns"] = columns
		report_data["result"] = data

		xlsx_data, column_widths = build_xlsx_data(columns, report_data, [], 1, ignore_visible_idx=True)
		xlsx_file = make_xlsx(xlsx_data, "Report", column_widths=column_widths)
		return xlsx_file.getvalue()

	elif format == "CSV":
		report_data = frappe._dict()
		report_data["columns"] = columns
		report_data["result"] = data

		xlsx_data, column_widths = build_xlsx_data(columns, report_data, [], 1, ignore_visible_idx=True)
		return to_csv(xlsx_data)

	else:
		frappe.throw(_("Invalid Output Format"))


def update_field_types(columns):
	for col in columns:
		if col.fieldtype in ("Link", "Dynamic Link", "Currency") and col.options != "Currency":
			col.fieldtype = "Data"
			col.options = ""
	return columns


def get_html_table(report, columns=None, data=None):
	return frappe.render_template(
		"templates/includes/report_to_pdf.html",
		{
			"title": report,
			"date_time": frappe.utils.now(),
			"columns": columns,
			"data": data
		}
	)


@frappe.whitelist()
def download_report_pdf(filters, report, format="PDF"):
	frappe.local.response.filecontent = get_report_content(filters, report, format)
	frappe.local.response.type = "download"
	frappe.local.response.filename = f"{report}-{frappe.generate_hash()}.{format.lower()}"

// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

frappe.ui.DocumentLock = class DocumentLock {
    constructor(opts) {
        $.extend(this, opts);
    }

    setup_document_lock(frm) {
        frappe.db.get_value(
            "Document Lock", { document_type: frm.doc.doctype, document: frm.doc.name }, "locked_by"
        ).then(r => {
            if (!r.exc && r.message && r.message.locked_by) {
                frm.dashboard.add_comment(
                    `<p class="text-danger">The form has been locked by ${r.message.locked_by}.</p>`,
                    "white",
                    true
                );

                if (r.message.locked_by != frappe.session.user) {
                    frappe.show_alert(__(`The form has been locked by ${r.message.locked_by}.`));
                    frm.set_read_only(true);
                    frm.refresh_fields();
                }
            }
        })
    }

    toggle_lock_unlock(frm) {
        frappe.db.get_value(
            "Document Lock", { document_type: frm.doc.doctype, document: frm.doc.name }, "locked_by"
        ).then(r => {
            if (!r.exc && r.message && r.message.locked_by) {
                
            }
        })
    }

    lock_document(frm) {
        if (frm.doc.__islocal) {
            return;
        }

        if (frm.is_dirty()) {
            frappe.show_alert(__("Please save before locking."));
            return;
        }

        frappe.call({
            method: "weassist.utils.doclock.lock_document",
            args: {
                doctype: frm.doc.doctype,
                docname: frm.doc.name
            }
        }).then(r => {
            if (r.message) {
                frappe.show_alert(__("The form has been locked succesfully."));
                frm.reload_doc();
            }
        });
    }


    unlock_document(frm) {
        if (frm.doc.__islocal) {
            return;
        }

        frappe.call({
            method: "weassist.utils.doclock.unlock_document",
            args: {
                doctype: frm.doc.doctype,
                docname: frm.doc.name
            }
        }).then(r => {
            if (r.message) {
                frappe.show_alert(__("The form has been unlocked succesfully."));
                frm.reload_doc();
            }
        });
    }
}
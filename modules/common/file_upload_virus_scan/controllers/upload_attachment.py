# -*- coding: utf-8 -*-
import email
import html
import json
import logging

from odoo import http
from odoo.addons.web.controllers.binary import Binary
from odoo.http import request

_log = logging.getLogger(__name__)

DEFAULT_ALLOWED_MIMETYPES = ['text/plain', 'application/pdf', 'application/msword']
BLACKLISTED_MIMETYPES = ['application/x-ms-dos-executable']


class ScanBinary(Binary):

    def get_allowed_mimetypes(self):
        # Step #1: validate mimetype
        # White list is configurable on the company record
        if request.env.company.allowed_mimetypes:
            allowed_mimetypes = [m.strip() for m in request.env.company.allowed_mimetypes.split(',')]
        else:
            allowed_mimetypes = DEFAULT_ALLOWED_MIMETYPES

        # Remove blacklisted extensions so they cannot even be added as a config
        return list(set(allowed_mimetypes) - set(BLACKLISTED_MIMETYPES))

    @http.route('/web/binary/upload_attachment', type='http', auth="user")
    def upload_attachment(self, model, id, ufile, callback=None):
        # Remove blacklisted extensions so they cannot even be added as a config
        allowed_mimetypes = self.get_allowed_mimetypes()

        if ufile.mimetype not in allowed_mimetypes:
            _log.error('Unexpected mimetype: {}'.format(ufile.mimetype))
            return self.prepare_error_return(ufile, callback, error_type='mimetype')

        ufile.filename = html.escape(ufile.filename)

        # Step #2: check for viruses
        # Note: .msg (Outlook email exports) have 'application/octet-stream' and it is a file object
        # In order to validate it, we need to read it first but then the file would be uploaded as blank
        # (as you can only read() once)
        # copy.deepcopy() is also not possible on FileStorage objects
        # So let's validate all other files first, then check for the message file
        if hasattr(ufile, 'getvalue') and ufile.mimetype != 'application/octet-stream':
            scan_ok, _other = request.env['ir.attachment'].scan_file(base64_content=ufile.getvalue())
            if not scan_ok:
                return self.prepare_error_return(ufile, callback, error_type='viruses')

        # Upload the file
        res = super(ScanBinary, self).upload_attachment(model, id, ufile, callback=callback)

        # Now time for a special handle of .msg files
        if ufile.mimetype == 'application/octet-stream':
            msg = email.message_from_string(str(ufile.read()))

            # Walk through and check all internal content
            for part in msg.walk():
                scan_ok, _other = request.env['ir.attachment'].scan_file(base64_content=part.get_payload(decode=True))
                if not scan_ok:
                    return self.prepare_error_return(ufile, callback, error_type='viruses')

        return res

    @staticmethod
    def prepare_error_return(ufile, callback, error_type='mimetype'):
        error_mapping = {
            'mimetype': 'The format of the file "{}" is not supported: {}. '
                        'Skipping the upload.'.format(ufile.filename, ufile.mimetype),
            'viruses': 'The file "{}" contains viruses! Skipping the upload.'.format(ufile.filename)
        }

        out = """<script language="javascript" type="text/javascript">
                    var win = window.top.window;
                    win.jQuery(win).trigger(%s, %s);
                </script>"""

        args = [{
            'error': error_mapping.get(error_type),
            'filename': ufile.filename,
            'mimetype': ufile.content_type,
            'id': -99,
            'size': 0.0
        }]

        return out % (json.dumps(callback.replace('\x3c', '')), json.dumps(args)) if callback else json.dumps(args)

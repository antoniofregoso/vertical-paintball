from odoo import tools
from odoo import api, fields, models

class PaintballReport(models.AbstractModel):
    _name = 'report.paintball.report_folio'
    _description = 'FolioReport'

    def _get_report_values(self, docids, data=None):
        docs = self.env['paintball.folio'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'paintball.folio',
            'docs': docs
        }

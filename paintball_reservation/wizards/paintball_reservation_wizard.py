# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PaintballReservationWizard(models.TransientModel):
    _name = 'paintball.reservation.wizard'
    _description = 'Allow to generate a reservation'

    date_start = fields.Datetime('Start Date', required=True)
    date_end = fields.Datetime('End Date', required=True)

    
    def report_reservation_detail(self):
        data = {
            'ids': self.ids,
            'model': 'paintball.reservation',
            'form': self.read(['date_start', 'date_end'])[0]
        }
        return self.env.ref('paintball_reservation.paintball_roomres_details'
                            ).report_action(self, data=data)

    
    def report_checkin_detail(self):
        data = {
            'ids': self.ids,
            'model': 'paintball.reservation',
            'form': self.read(['date_start', 'date_end'])[0],
        }
        return self.env.ref('paintball_reservation.paintball_checkin_details'
                            ).report_action(self, data=data)

    
    def report_checkout_detail(self):
        data = {
            'ids': self.ids,
            'model': 'paintball.reservation',
            'form': self.read(['date_start', 'date_end'])[0]
        }
        return self.env.ref('paintball_reservation.paintball_checkout_details'
                            ).report_action(self, data=data)

    
    def report_maxroom_detail(self):
        data = {
            'ids': self.ids,
            'model': 'paintball.reservation',
            'form': self.read(['date_start', 'date_end'])[0]
        }
        return self.env.ref('paintball_reservation.paintball_maxroom_details'
                            ).report_action(self, data=data)


class MakeFolioWizard(models.TransientModel):
    _name = 'wizard.make.folio'
    _description = 'Allow to generate the folio'

    grouped = fields.Boolean('Group the Folios')

    
    def makeFolios(self):
        order_obj = self.env['paintball.reservation']
        newinv = []
        for order in order_obj.browse(self.env.context.get('active_ids', [])):
            for folio in order.folio_id:
                newinv.append(folio.id)
        return {
            'domain': "[('id','in', [" + ','.join(map(str, newinv)) + "])]",
            'name': 'Folios',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'paintball.folio',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }

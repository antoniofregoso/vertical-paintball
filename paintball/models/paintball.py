# -*- coding: utf-8 -*-

import time
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models, _

def _offset_format_timestamp1(src_tstamp_str, src_format, dst_format,
                              ignore_unparsable_time=True, context=None):
    """
    Convert a source timeStamp string into a destination timeStamp string,
    attempting to apply the correct offset if both the server and local
    timeZone are recognized,or no offset at all if they aren't or if
    tz_offset is false (i.e. assuming they are both in the same TZ).

    @param src_tstamp_str: the STR value containing the timeStamp.
    @param src_format: the format to use when parsing the local timeStamp.
    @param dst_format: the format to use when formatting the resulting
     timeStamp.
    @param server_to_client: specify timeZone offset direction (server=src
                             and client=dest if True, or client=src and
                             server=dest if False)
    @param ignore_unparsable_time: if True, return False if src_tstamp_str
                                   cannot be parsed using src_format or
                                   formatted using dst_format.
    @return: destination formatted timestamp, expressed in the destination
             timezone if possible and if tz_offset is true, or src_tstamp_str
             if timezone offset could not be determined.
    """
    if not src_tstamp_str:
        return False
    res = src_tstamp_str
    if src_format and dst_format:
        try:
            # dt_value needs to be a datetime object\
            # (so notime.struct_time or mx.DateTime.DateTime here!)
            dt_value = datetime.strptime(src_tstamp_str, src_format)
            if context.get('tz', False):
                try:
                    import pytz
                    src_tz = pytz.timezone(context['tz'])
                    dst_tz = pytz.timezone('UTC')
                    src_dt = src_tz.localize(dt_value, is_dst=True)
                    dt_value = src_dt.astimezone(dst_tz)
                except Exception:
                    pass
            res = dt_value.strftime(dst_format)
        except Exception:
            # Normal ways to end up here are if strptime or strftime failed
            if not ignore_unparsable_time:
                return False
            pass
    return res


class PaintballAmenityType(models.Model):

    _name = "paintball.amenity.type"
    _description = "Amenity Type"

    name = fields.Char(required=True)
    
class ProductProduct(models.Model):

    _inherit = "product.product"

    isamenity = fields.Boolean('Is Room')
    isservice = fields.Boolean('Is Service')
    
class FolioAmenityLine(models.Model):

    _name = 'folio.amenity.line'
    _description = 'Paintball Amenity Reservation'
    _rec_name = 'amenity_id'

    amenity_id = fields.Many2one('paintball.amenity', 'Amenity id')
    check_in = fields.Datetime('Check In Date', required=True)
    check_out = fields.Datetime('Check Out Date', required=True)
    folio_id = fields.Many2one('paintball.folio', string='Folio Number')
    state = fields.Selection(string='state', related='folio_id.state')
    

class PaintballAmenity(models.Model):

    _name = 'paintball.amenity'
    _description = 'Paintball Amenity'

    product_id = fields.Many2one('product.product', 'Product_id',
                                 required=True, delegate=True,
                                 ondelete='cascade')
    max_shooters = fields.Integer()
    min_shooters = fields.Integer()
    categ_id = fields.Many2one('paintball.amenity.type', string='Amenity Category',
                               required=True)
    state = fields.Selection([('available', 'Available'),
                               ('occupied', 'Occupied')],
                              'State', default='available')
    capacity = fields.Integer('Capacity', required=True)
    amenity_line_ids = fields.One2many('folio.amenity.line', 'amenity_id',
                                    string='Amenity Reservation Line')
    product_manager = fields.Many2one('res.users', 'Product Manager')

    @api.constrains('capacity')
    def check_capacity(self):
        for amenity in self:
            if amenity.capacity <= 0:
                raise ValidationError(_('Amenity capacity must be more than 0'))

    @api.onchange('isamenity')
    def isroom_change(self):
        '''
        Based on isroom, state will be updated.
        ----------------------------------------
        @param self: object pointer
        '''
        if self.isamenity is False:
            self.state = 'occupied'
        if self.isamenity is True:
            self.state = 'available'


    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if 'isamenity' in vals and vals['isamenity'] is False:
            vals.update({'color': 2, 'state': 'occupied'})
        if 'isamenity'in vals and vals['isamenity'] is True:
            vals.update({'color': 5, 'state': 'available'})
        ret_val = super(PaintballAmenity, self).write(vals)
        return ret_val


    def set_amenity_state_occupied(self):
        """
        This method is used to change the state
        to occupied of the paintball amenity.
        ---------------------------------------
        @param self: object pointer
        """
        return self.write({'isamenity': False, 'color': 2})


    def set_amenity_state_available(self):
        """
        This method is used to change the state
        to available of the hotel room.
        ---------------------------------------
        @param self: object pointer
        """
        return self.write({'isamenity': True, 'color': 5})
    
 
 
class HotelFolio(models.Model):

    _name = 'hotel.folio'
    _description = 'hotel folio new'
    _rec_name = 'order_id'
    _order = 'id'
    
    
    name = fields.Char('Folio Number', readonly=True, index=True,
                       default='New')
    order_id = fields.Many2one('sale.order', 'Order', delegate=True,
                               required=True, ondelete='cascade')
    checkin_date = fields.Datetime('Check In', required=True, readonly=True,
                                   states={'draft': [('readonly', False)]},
                                   default=_get_checkin_date)
    checkout_date = fields.Datetime('Check Out', required=True, readonly=True,
                                    states={'draft': [('readonly', False)]},
                                    default=_get_checkout_date)
    room_lines = fields.One2many('hotel.folio.line', 'folio_id',
                                 readonly=True,
                                 states={'draft': [('readonly', False)],
                                         'sent': [('readonly', False)]},
                                 help="Hotel room reservation detail.")
    service_lines = fields.One2many('hotel.service.line', 'folio_id',
                                    readonly=True,
                                    states={'draft': [('readonly', False)],
                                            'sent': [('readonly', False)]},
                                    help="Hotel services details provided to"
                                    "Customer and it will included in "
                                    "the main Invoice.")
    hotel_policy = fields.Selection([('prepaid', 'On Booking'),
                                     ('manual', 'On Check In'),
                                     ('picking', 'On Checkout')],
                                    'Hotel Policy', default='manual',
                                    help="Hotel policy for payment that "
                                    "either the guest has to payment at "
                                    "booking time or check-in "
                                    "check-out time.")
    duration = fields.Float('Duration in Days',
                            help="Number of days which will automatically "
                            "count from the check-in and check-out date. ")
    hotel_invoice_id = fields.Many2one('account.invoice', 'Invoice',
                                       copy=False)
    duration_dummy = fields.Float('Duration Dummy')
    
    
class HotelFolioLine(models.Model):

    _name = 'hotel.folio.line'
    _description = 'hotel folio1 room line'
    
    order_line_id = fields.Many2one('sale.order.line', string='Order Line',
                                    required=True, delegate=True,
                                    ondelete='cascade')
    folio_id = fields.Many2one('hotel.folio', string='Folio',
                               ondelete='cascade')
    checkin_date = fields.Datetime(string='Check In', required=True,
                                   default=_get_checkin_date)
    checkout_date = fields.Datetime(string='Check Out', required=True,
                                    default=_get_checkout_date)
    is_reserved = fields.Boolean(string='Is Reserved',
                                 help='True when folio line created from \
                                 Reservation')

   




# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


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


class PaintballArea(models.Model):

    _name = "paintball.area"
    _description = "Area"

    name = fields.Char('Area Name', required=True, index=True)
    sequence = fields.Integer(index=True)


class PaintballZoneType(models.Model):

    _name = "paintball.zone.type"
    _description = "Zone Type"

    name = fields.Char(required=True)
    categ_id = fields.Many2one('paintball.zone.type', 'Category')
    child_ids = fields.One2many('paintball.zone.type', 'categ_id',
                                'Child Categories')


    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.categ_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.categ_id
            return res
        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            # Be sure name_search is symmetric to name_get
            category_names = name.split(' / ')
            parents = list(category_names)
            child = parents.pop()
            domain = [('name', operator, child)]
            if parents:
                names_ids = self.name_search(' / '.join(parents), args=args,
                                             operator='ilike', limit=limit)
                category_ids = [name_id[0] for name_id in names_ids]
                if operator in expression.NEGATIVE_TERM_OPERATORS:
                    categories = self.search([('id', 'not in', category_ids)])
                    domain = expression.OR([[('categ_id', 'in',
                                              categories.ids)], domain])
                else:
                    domain = expression.AND([[('categ_id', 'in',
                                               category_ids)], domain])
                for i in range(1, len(category_names)):
                    domain = [[('name', operator,
                                ' / '.join(category_names[-1 - i:]))], domain]
                    if operator in expression.NEGATIVE_TERM_OPERATORS:
                        domain = expression.AND(domain)
                    else:
                        domain = expression.OR(domain)
            categories = self.search(expression.AND([domain, args]),
                                     limit=limit)
        else:
            categories = self.search(args, limit=limit)
        return categories.name_get()


class ProductProduct(models.Model):

    _inherit = "product.product"

    iszone = fields.Boolean('Is Zone')
    iscategid = fields.Boolean('Is Categ')
    isservice = fields.Boolean('Is Service')
    



class PaintballZoneAmenitiesType(models.Model):

    _name = 'paintball.zone.amenities.type'
    _description = 'amenities Type'

    name = fields.Char(required=True)
    amenity_id = fields.Many2one('paintball.zone.amenities.type', 'Category')
    child_ids = fields.One2many('paintball.zone.amenities.type', 'amenity_id',
                                'Child Categories')


    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.amenity_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.amenity_id
            return res
        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            # Be sure name_search is symetric to name_get
            category_names = name.split(' / ')
            parents = list(category_names)
            child = parents.pop()
            domain = [('name', operator, child)]
            if parents:
                names_ids = self.name_search(' / '.join(parents), args=args,
                                             operator='ilike', limit=limit)
                category_ids = [name_id[0] for name_id in names_ids]
                if operator in expression.NEGATIVE_TERM_OPERATORS:
                    categories = self.search([('id', 'not in', category_ids)])
                    domain = expression.OR([[('amenity_id', 'in',
                                              categories.ids)], domain])
                else:
                    domain = expression.AND([[('amenity_id', 'in',
                                               category_ids)], domain])
                for i in range(1, len(category_names)):
                    domain = [[('name', operator,
                                ' / '.join(category_names[-1 - i:]))], domain]
                    if operator in expression.NEGATIVE_TERM_OPERATORS:
                        domain = expression.AND(domain)
                    else:
                        domain = expression.OR(domain)
            categories = self.search(expression.AND([domain, args]),
                                     limit=limit)
        else:
            categories = self.search(args, limit=limit)
        return categories.name_get()


class PaintballZoneAmenities(models.Model):

    _name = 'paintball.zone.amenities'
    _description = 'Zone amenities'

    product_id = fields.Many2one('product.product', 'Product Category',
                                 required=True, delegate=True,
                                 ondelete='cascade')
    categ_id = fields.Many2one('paintball.zone.amenities.type',
                               string='Amenities Category', required=True)
    product_manager = fields.Many2one('res.users', string='Product Manager')


class FolioZoneLine(models.Model):

    _name = 'folio.zone.line'
    _description = 'Paintball Zone Reservation'
    _rec_name = 'zone_id'

    zone_id = fields.Many2one('paintball.zone', 'Zone id')
    check_in = fields.Datetime('Check In Date', required=True)
    check_out = fields.Datetime('Check Out Date', required=True)
    folio_id = fields.Many2one('paintball.folio', string='Folio Number')
    status = fields.Selection(string='state', related='folio_id.state')


class PaintballZone(models.Model):

    _name = 'paintball.zone'
    _description = 'Paintball Zone'

    product_id = fields.Many2one('product.product', 'Product_id',
                                 required=True, delegate=True,
                                 ondelete='cascade')
    area_id = fields.Many2one('paintball.area', 'Area Name',
                               help='At which area the zone is located.')
    max_adult = fields.Integer()
    max_child = fields.Integer()
    categ_id = fields.Many2one('paintball.zone.type', string='Zone Category',
                               required=True)
    zone_amenities = fields.Many2many('paintball.zone.amenities', 'temp_tab',
                                      'zone_amenities', 'rcateg_id',
                                      help='List of zone amenities. ')
    status = fields.Selection([('available', 'Available'),
                               ('occupied', 'Occupied')],
                              'Status', default='available')
    capacity = fields.Integer('Max Capacity', required=True)
    capacity_min = fields.Integer('Min Capacity', required=True)
    zone_line_ids = fields.One2many('folio.zone.line', 'zone_id',
                                    string='Zone Reservation Line')
    product_manager = fields.Many2one('res.users', 'Product Manager')

    @api.constrains('capacity')
    def check_capacity(self):
        for zone in self:
            if zone.capacity <= 0:
                raise ValidationError(_('Zone capacity must be more than 0'))

    @api.onchange('iszone')
    def iszone_change(self):
        '''
        Based on iszone, status will be updated.
        ----------------------------------------
        @param self: object pointer
        '''
        if self.iszone is False:
            self.status = 'occupied'
        if self.iszone is True:
            self.status = 'available'


    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if 'iszone' in vals and vals['iszone'] is False:
            vals.update({'color': 2, 'status': 'occupied'})
        if 'iszone'in vals and vals['iszone'] is True:
            vals.update({'color': 5, 'status': 'available'})
        ret_val = super(PaintballZone, self).write(vals)
        return ret_val


    def set_zone_status_occupied(self):
        """
        This method is used to change the state
        to occupied of the paintball zone.
        ---------------------------------------
        @param self: object pointer
        """
        return self.write({'iszone': False, 'color': 2})


    def set_zone_status_available(self):
        """
        This method is used to change the state
        to available of the paintball zone.
        ---------------------------------------
        @param self: object pointer
        """
        return self.write({'iszone': True, 'color': 5})


class PaintballFolio(models.Model):

    _name = 'paintball.folio'
    _description = 'paintball folio new'
    _rec_name = 'order_id'
    _order = 'id'


    def name_get(self):
        res = []
        disp = ''
        for rec in self:
            if rec.order_id:
                disp = str(rec.name)
                res.append((rec.id, disp))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        args += ([('name', operator, name)])
        mids = self.search(args, limit=100)
        return mids.name_get()

    @api.model
    def _needaction_count(self, domain=None):
        """
         Show a count of draft state folio on the menu badge.
         @param self: object pointer
        """
        return self.search_count([('state', '=', 'draft')])

    @api.model
    def _get_checkin_date(self):
        if self._context.get('tz'):
            to_zone = self._context.get('tz')
        else:
            to_zone = 'UTC'
        return _offset_format_timestamp1(time.strftime("%Y-%m-%d 12:00:00"),
                                         DEFAULT_SERVER_DATETIME_FORMAT,
                                         DEFAULT_SERVER_DATETIME_FORMAT,
                                         ignore_unparsable_time=True,
                                         context={'tz': to_zone})

    @api.model
    def _get_checkout_date(self):
        if self._context.get('tz'):
            to_zone = self._context.get('tz')
        else:
            to_zone = 'UTC'
        tm_delta = timedelta(days=1)
        return datetime.strptime(_offset_format_timestamp1
                                 (time.strftime("%Y-%m-%d 12:00:00"),
                                  DEFAULT_SERVER_DATETIME_FORMAT,
                                  DEFAULT_SERVER_DATETIME_FORMAT,
                                  ignore_unparsable_time=True,
                                  context={'tz': to_zone}),
                                 '%Y-%m-%d %H:%M:%S') + tm_delta


    def copy(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        return super(PaintballFolio, self).copy(default=default)

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
    zone_lines = fields.One2many('paintball.folio.line', 'folio_id',
                                 readonly=True,
                                 states={'draft': [('readonly', False)],
                                         'sent': [('readonly', False)]},
                                 help="Paintball zone reservation detail.")
    service_lines = fields.One2many('paintball.service.line', 'folio_id',
                                    readonly=True,
                                    states={'draft': [('readonly', False)],
                                            'sent': [('readonly', False)]},
                                    help="Paintball services details provided to"
                                    "Customer and it will included in "
                                    "the main Invoice.")
    paintball_policy = fields.Selection([('prepaid', 'On Booking'),
                                     ('manual', 'On Check In'),
                                     ('picking', 'On Checkout')],
                                    'Paintball Policy', default='manual',
                                    help="Paintball policy for payment that "
                                    "either the guest has to payment at "
                                    "booking time or check-in "
                                    "check-out time.")
    duration = fields.Float('Duration in Days',
                            help="Number of days which will automatically "
                            "count from the check-in and check-out date. ")
    paintball_invoice_id = fields.Many2one('account.move', 'Invoice',
                                       copy=False)
    duration_dummy = fields.Float('Duration Dummy')
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    
    @api.constrains('zone_lines')
    def folio_zone_lines(self):
        '''
        This method is used to validate the zone_lines.
        ------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        folio_zones = []
        for zone in self[0].zone_lines:
            if zone.product_id.id in folio_zones:
                raise ValidationError(_('You Cannot Take Same Zone Twice'))
            folio_zones.append(zone.product_id.id)

    @api.onchange('checkout_date', 'checkin_date')
    def onchange_dates(self):
        '''
        This method gives the duration between check in and checkout
        if customer will leave only for some hour it would be considers
        as a whole day.If customer will check in checkout for more or equal
        hours, which configured in company as additional hours than it would
        be consider as full days
        --------------------------------------------------------------------
        @param self: object pointer
        @return: Duration and checkout_date
        '''
        configured_addition_hours = 0
        wid = self.warehouse_id
        whouse_com_id = wid or wid.company_id
        if whouse_com_id:
            configured_addition_hours = wid.company_id.additional_hours
        myduration = 0
        if self.checkout_date and self.checkin_date:
            dur = self.checkin_date - self.checkin_date
            sec_dur = dur.seconds
            if (not dur.days and not sec_dur) or (dur.days and not sec_dur):
                myduration = dur.days
            else:
                myduration = dur.days + 1
            # To calculate additional hours in paintball zone as per minutes
            if configured_addition_hours > 0:
                additional_hours = abs((dur.seconds / 60) / 60)
                if additional_hours >= configured_addition_hours:
                    myduration += 1
        self.duration = myduration
        self.duration_dummy = self.duration

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for paintball folio.
        """
        if not 'service_lines' and 'folio_id' in vals:
            tmp_zone_lines = vals.get('zone_lines', [])
            vals['order_policy'] = vals.get('paintball_policy', 'manual')
            vals.update({'zone_lines': []})
            folio_id = super(PaintballFolio, self).create(vals)
            for line in (tmp_zone_lines):
                line[2].update({'folio_id': folio_id.id})
            vals.update({'zone_lines': tmp_zone_lines})
            folio_id.write(vals)
        else:
            if not vals:
                vals = {}
            vals['name'] = self.env['ir.sequence'].next_by_code('paintball.folio')
            vals['duration'] = vals.get('duration',
                                        0.0) or vals.get('duration_dummy',
                                                         0.0)
            folio_id = super(PaintballFolio, self).create(vals)
            folio_zone_line_obj = self.env['folio.zone.line']
            h_zone_obj = self.env['paintball.zone']
            try:
                for rec in folio_id:
                    if not rec.reservation_id:
                        for zone_rec in rec.zone_lines:
                            prod = zone_rec.product_id.name
                            zone_obj = h_zone_obj.search([('name', '=',
                                                           prod)])
                            zone_obj.write({'iszone': False})
                            vals = {'zone_id': zone_obj.id,
                                    'check_in': rec.checkin_date,
                                    'check_out': rec.checkout_date,
                                    'folio_id': rec.id,
                                    }
                            folio_zone_line_obj.create(vals)
            except:
                for rec in folio_id:
                    for zone_rec in rec.zone_lines:
                        prod = zone_rec.product_id.name
                        zone_obj = h_zone_obj.search([('name', '=', prod)])
                        zone_obj.write({'iszone': False})
                        vals = {'zone_id': zone_obj.id,
                                'check_in': rec.checkin_date,
                                'check_out': rec.checkout_date,
                                'folio_id': rec.id,
                                }
                        folio_zone_line_obj.create(vals)
        return folio_id


    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        product_obj = self.env['product.product']
        h_zone_obj = self.env['paintball.zone']
        folio_zone_line_obj = self.env['folio.zone.line']
        zone_lst = []
        zone_lst1 = []
        for rec in self:
            for res in rec.zone_lines:
                zone_lst1.append(res.product_id.id)
            if vals and vals.get('duration_dummy', False):
                vals['duration'] = vals.get('duration_dummy', 0.0)
            else:
                vals['duration'] = rec.duration
            for folio_rec in rec.zone_lines:
                zone_lst.append(folio_rec.product_id.id)
            new_zones = set(zone_lst).difference(set(zone_lst1))
            if len(list(new_zones)) != 0:
                zone_list = product_obj.browse(list(new_zones))
                for rm in zone_list:
                    zone_obj = h_zone_obj.search([('name', '=', rm.name)])
                    zone_obj.write({'iszone': False})
                    vals = {'zone_id': zone_obj.id,
                            'check_in': rec.checkin_date,
                            'check_out': rec.checkout_date,
                            'folio_id': rec.id,
                            }
                    folio_zone_line_obj.create(vals)
            if len(list(new_zones)) == 0:
                zone_list_obj = product_obj.browse(zone_lst1)
                for rom in zone_list_obj:
                    zone_obj = h_zone_obj.search([('name', '=', rom.name)])
                    zone_obj.write({'iszone': False})
                    zone_vals = {'zone_id': zone_obj.id,
                                 'check_in': rec.checkin_date,
                                 'check_out': rec.checkout_date,
                                 'folio_id': rec.id,
                                 }
                    folio_romline_rec = (folio_zone_line_obj.search
                                         ([('folio_id', '=', rec.id)]))
                    folio_romline_rec.write(zone_vals)
        return super(PaintballFolio, self).write(vals)



    @api.onchange('partner_id')
    def onchange_partner_id(self):
        '''
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the paintball folio as well
        ---------------------------------------------------------------
        @param self: object pointer
        '''
        if self.partner_id:
            partner_rec = self.env['res.partner'].browse(self.partner_id.id)
            order_ids = [folio.order_id.id for folio in self]
            if not order_ids:
                self.partner_invoice_id = partner_rec.id
                self.partner_shipping_id = partner_rec.id
                self.pricelist_id = partner_rec.property_product_pricelist.id
                raise _('Not Any Order For  %s ' % (partner_rec.name))
            else:
                self.partner_invoice_id = partner_rec.id
                self.partner_shipping_id = partner_rec.id
                self.pricelist_id = partner_rec.property_product_pricelist.id


    def action_done(self):
        self.state = 'done'


    def action_invoice_create(self, grouped=False, final=False):
        '''
        @param self: object pointer
        '''
        zone_lst = []
        invoice_id = (self.order_id.action_invoice_create(grouped=False,
                                                          final=False))
        for line in self:
            values = {'invoiced': True,
                      'paintball_invoice_id': invoice_id
                      }
            line.write(values)
            for rec in line.zone_lines:
                zone_lst.append(rec.product_id)
            for zone in zone_lst:
                zone_rec = self.env['paintball.zone'].\
                    search([('name', '=', zone.name)])
                zone_rec.write({'iszone': True})
        return invoice_id


    def action_invoice_cancel(self):
        '''
        @param self: object pointer
        '''
        if not self.order_id:
            raise UserError(_('Order id is not available'))
        for sale in self:
            for line in sale.order_line:
                line.write({'invoiced': 'invoiced'})
        self.state = 'invoice_except'
        return self.order_id.action_invoice_cancel


    def action_cancel(self):
        '''
        @param self: object pointer
        '''
        if not self.order_id:
            raise UserError(_('Order id is not available'))
        for sale in self:
            for invoice in sale.invoice_ids:
                invoice.state = 'cancel'
        return self.order_id.action_cancel()


    def action_confirm(self):
        for order in self.order_id:
            order.state = 'sale'
            if not order.analytic_account_id:
                for line in order.order_line:
                    if line.product_id.invoice_policy == 'cost':
                        order._create_analytic_account()
                        break
        config_parameter_obj = self.env['ir.config_parameter']
        if config_parameter_obj.sudo().get_param('sale.auto_done_setting'):
            self.order_id.action_done()


    def test_state(self, mode):
        '''
        @param self: object pointer
        @param mode: state of workflow
        '''
        write_done_ids = []
        write_cancel_ids = []
        if write_done_ids:
            test_obj = self.env['sale.order.line'].browse(write_done_ids)
            test_obj.write({'state': 'done'})
        if write_cancel_ids:
            test_obj = self.env['sale.order.line'].browse(write_cancel_ids)
            test_obj.write({'state': 'cancel'})


    def action_cancel_draft(self):
        '''
        @param self: object pointer
        '''
        if not len(self._ids):
            return False
        query = "select id from sale_order_line \
        where order_id IN %s and state=%s"
        self._cr.execute(query, (tuple(self._ids), 'cancel'))
        cr1 = self._cr
        line_ids = map(lambda x: x[0], cr1.fetchall())
        self.write({'state': 'draft', 'invoice_ids': [], 'shipped': 0})
        sale_line_obj = self.env['sale.order.line'].browse(line_ids)
        sale_line_obj.write({'invoiced': False, 'state': 'draft',
                             'invoice_lines': [(6, 0, [])]})
        return True


class PaintballFolioLine(models.Model):

    _name = 'paintball.folio.line'
    _description = 'paintball folio1 zone line'


    def copy(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        return super(PaintballFolioLine, self).copy(default=default)

    @api.model
    def _get_checkin_date(self):
        if 'checkin' in self._context:
            return self._context['checkin']
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _get_checkout_date(self):
        if 'checkout' in self._context:
            return self._context['checkout']
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    order_line_id = fields.Many2one('sale.order.line', string='Order Line',
                                    required=True, delegate=True,
                                    ondelete='cascade')
    folio_id = fields.Many2one('paintball.folio', string='Folio',
                               ondelete='cascade')
    checkin_date = fields.Datetime(string='Check In', required=True,
                                   default=_get_checkin_date)
    checkout_date = fields.Datetime(string='Check Out', required=True,
                                    default=_get_checkout_date)
    is_reserved = fields.Boolean(string='Is Reserved',
                                 help='True when folio line created from \
                                 Reservation')

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for paintball folio line.
        """
        if 'folio_id' in vals:
            folio = self.env["paintball.folio"].browse(vals['folio_id'])
            vals.update({'order_id': folio.order_id.id})
        return super(PaintballFolioLine, self).create(vals)

    @api.constrains('checkin_date', 'checkout_date')
    def check_dates(self):
        '''
        This method is used to validate the checkin_date and checkout_date.
        -------------------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        if self.checkin_date >= self.checkout_date:
                raise ValidationError(_('Zone line Check In Date Should be \
                less than the Check Out Date!'))
        if self.folio_id.date_order and self.checkin_date:
            if self.checkin_date <= self.folio_id.date_order:
                raise ValidationError(_('Zone line check in date should be \
                greater than the current date.'))


    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        sale_line_obj = self.env['sale.order.line']
        fr_obj = self.env['folio.zone.line']
        for line in self:
            if line.order_line_id:
                sale_unlink_obj = (sale_line_obj.browse
                                   ([line.order_line_id.id]))
                for rec in sale_unlink_obj:
                    zone_obj = self.env['paintball.zone'
                                        ].search([('name', '=', rec.name)])
                    if zone_obj.id:
                        folio_arg = [('folio_id', '=', line.folio_id.id),
                                     ('zone_id', '=', zone_obj.id)]
                        folio_zone_line_myobj = fr_obj.search(folio_arg)
                        if folio_zone_line_myobj.id:
                            folio_zone_line_myobj.unlink()
                            zone_obj.write({'iszone': True,
                                            'status': 'available'})
                sale_unlink_obj.unlink()
        return super(PaintballFolioLine, self).unlink()

    @api.onchange('product_id')
    def product_id_change(self):
        '''
 -        @param self: object pointer
 -        '''
        context = dict(self._context)
        if not context:
            context = {}
        if context.get('folio', False):
            if self.product_id and self.folio_id.partner_id:
                self.name = self.product_id.name
                self.price_unit = self.product_id.list_price
                self.product_uom = self.product_id.uom_id
                tax_obj = self.env['account.tax']
                pr = self.product_id
                self.price_unit = tax_obj._fix_tax_included_price(pr.price,
                                                                  pr.taxes_id,
                                                                  self.tax_id)
        else:
            if not self.product_id:
                return {'domain': {'product_uom': []}}
            val = {}
            pr = self.product_id.with_context(
                lang=self.folio_id.partner_id.lang,
                partner=self.folio_id.partner_id.id,
                quantity=val.get('product_uom_qty') or self.product_uom_qty,
                date=self.folio_id.date_order,
                pricelist=self.folio_id.pricelist_id.id,
                uom=self.product_uom.id
            )
            p = pr.with_context(pricelist=self.order_id.pricelist_id.id).price
            if self.folio_id.pricelist_id and self.folio_id.partner_id:
                obj = self.env['account.tax']
                val['price_unit'] = obj._fix_tax_included_price(p,
                                                                pr.taxes_id,
                                                                self.tax_id)

    @api.onchange('checkin_date', 'checkout_date')
    def on_change_checkout(self):
        '''
        When you change checkin_date or checkout_date it will checked it
        and update the qty of paintball folio line
        -----------------------------------------------------------------
        @param self: object pointer
        '''
        configured_addition_hours = 0
        fwhouse_id = self.folio_id.warehouse_id
        fwc_id = fwhouse_id or fwhouse_id.company_id
        if fwc_id:
            configured_addition_hours = fwhouse_id.company_id.additional_hours
        myduration = 0
        if not self.checkin_date:
            self.checkin_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not self.checkout_date:
            self.checkout_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if self.checkin_date and self.checkout_date:
            dur = self.checkout_date - self.checkin_date
            sec_dur = dur.seconds
            if (not dur.days and not sec_dur) or (dur.days and not sec_dur):
                myduration = dur.days
            else:
                myduration = dur.days + 1
#            To calculate additional hours in paintball zone as per minutes
            if configured_addition_hours > 0:
                additional_hours = abs((dur.seconds / 60) / 60)
                if additional_hours >= configured_addition_hours:
                    myduration += 1
        self.product_uom_qty = myduration
        paintball_zone_obj = self.env['paintball.zone']
        paintball_zone_ids = paintball_zone_obj.search([])
        avail_prod_ids = []
        for zone in paintball_zone_ids:
            assigned = False
            for rm_line in zone.zone_line_ids:
                if rm_line.status != 'cancel':
                    if(self.checkin_date <= rm_line.check_in <=
                       self.checkout_date) or (self.checkin_date <=
                                               rm_line.check_out <=
                                               self.checkout_date):
                        assigned = True
                    elif (rm_line.check_in <= self.checkin_date <=
                          rm_line.check_out) or (rm_line.check_in <=
                                                 self.checkout_date <=
                                                 rm_line.check_out):
                        assigned = True
            if not assigned:
                avail_prod_ids.append(zone.product_id.id)
        domain = {'product_id': [('id', 'in', avail_prod_ids)]}
        return {'domain': domain}


    def button_confirm(self):
        '''
        @param self: object pointer
        '''
        for folio in self:
            line = folio.order_line_id
            line.button_confirm()
        return True


    def button_done(self):
        '''
        @param self: object pointer
        '''
        lines = [folio_line.order_line_id for folio_line in self]
        lines.button_done()
        self.state = 'done'
        return True


    def copy_data(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        line_id = self.order_line_id.id
        sale_line_obj = self.env['sale.order.line'].browse(line_id)
        return sale_line_obj.copy_data(default=default)


class PaintballServiceLine(models.Model):

    _name = 'paintball.service.line'
    _description = 'paintball Service line'


    def copy(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        return super(PaintballServiceLine, self).copy(default=default)

    @api.model
    def _service_checkin_date(self):
        if 'checkin' in self._context:
            return self._context['checkin']
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _service_checkout_date(self):
        if 'checkout' in self._context:
            return self._context['checkout']
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    service_line_id = fields.Many2one('sale.order.line', 'Service Line',
                                      required=True, delegate=True,
                                      ondelete='cascade')
    folio_id = fields.Many2one('paintball.folio', 'Folio', ondelete='cascade')
    ser_checkin_date = fields.Datetime('From Date', required=True,
                                       default=_service_checkin_date)
    ser_checkout_date = fields.Datetime('To Date', required=True,
                                        default=_service_checkout_date)

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for paintball service line.
        """
        if 'folio_id' in vals:
            folio = self.env['paintball.folio'].browse(vals['folio_id'])
            vals.update({'order_id': folio.order_id.id})
        return super(PaintballServiceLine, self).create(vals)


    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        s_line_obj = self.env['sale.order.line']
        for line in self:
            if line.service_line_id:
                sale_unlink_obj = s_line_obj.browse([line.service_line_id.id])
                sale_unlink_obj.unlink()
        return super(PaintballServiceLine, self).unlink()

    @api.onchange('product_id')
    def product_id_change(self):
        '''
        @param self: object pointer
        '''
        if self.product_id and self.folio_id.partner_id:
            self.name = self.product_id.name
            self.price_unit = self.product_id.list_price
            self.product_uom = self.product_id.uom_id
            tax_obj = self.env['account.tax']
            prod = self.product_id
            self.price_unit = tax_obj._fix_tax_included_price(prod.price,
                                                              prod.taxes_id,
                                                              self.tax_id)

    @api.onchange('ser_checkin_date', 'ser_checkout_date')
    def on_change_checkout(self):
        '''
        When you change checkin_date or checkout_date it will checked it
        and update the qty of paintball service line
        -----------------------------------------------------------------
        @param self: object pointer
        '''
        if not self.ser_checkin_date:
            time_a = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            self.ser_checkin_date = time_a
        if not self.ser_checkout_date:
            self.ser_checkout_date = time_a
        if self.ser_checkout_date < self.ser_checkin_date:
            raise _('Checkout must be greater or equal checkin date')
        if self.ser_checkin_date and self.ser_checkout_date:
            diffDate = self.ser_checkout_date - self.ser_checkin_date
            qty = diffDate.days + 1
            self.product_uom_qty = qty


    def button_confirm(self):
        '''
        @param self: object pointer
        '''
        for folio in self:
            line = folio.service_line_id
            x = line.button_confirm()
        return x


    def button_done(self):
        '''
        @param self: object pointer
        '''
        for folio in self:
            line = folio.service_line_id
            x = line.button_done()
        return x


    def copy_data(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        sale_line_obj = self.env['sale.order.line'
                                 ].browse(self.service_line_id.id)
        return sale_line_obj.copy_data(default=default)


class PaintballServiceType(models.Model):

    _name = "paintball.service.type"
    _description = "Service Type"

    name = fields.Char('Service Name', size=64, required=True)
    service_id = fields.Many2one('paintball.service.type', 'Service Category')
    child_ids = fields.One2many('paintball.service.type', 'service_id',
                                'Child Categories')


    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.service_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.service_id
            return res
        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            # Be sure name_search is symetric to name_get
            category_names = name.split(' / ')
            parents = list(category_names)
            child = parents.pop()
            domain = [('name', operator, child)]
            if parents:
                names_ids = self.name_search(' / '.join(parents), args=args,
                                             operator='ilike', limit=limit)
                category_ids = [name_id[0] for name_id in names_ids]
                if operator in expression.NEGATIVE_TERM_OPERATORS:
                    categories = self.search([('id', 'not in', category_ids)])
                    domain = expression.OR([[('service_id', 'in',
                                              categories.ids)], domain])
                else:
                    domain = expression.AND([[('service_id', 'in',
                                               category_ids)], domain])
                for i in range(1, len(category_names)):
                    domain = [[('name', operator,
                                ' / '.join(category_names[-1 - i:]))], domain]
                    if operator in expression.NEGATIVE_TERM_OPERATORS:
                        domain = expression.AND(domain)
                    else:
                        domain = expression.OR(domain)
            categories = self.search(expression.AND([domain, args]),
                                     limit=limit)
        else:
            categories = self.search(args, limit=limit)
        return categories.name_get()


class PaintballServices(models.Model):

    _name = 'paintball.services'
    _description = 'Paintball Services and its charges'

    product_id = fields.Many2one('product.product', 'Service_id',
                                 required=True, ondelete='cascade',
                                 delegate=True)
    categ_id = fields.Many2one('paintball.service.type', string='Service Category',
                               required=True)
    product_manager = fields.Many2one('res.users', string='Product Manager')


class ResCompany(models.Model):

    _inherit = 'res.company'

    additional_hours = fields.Integer('Additional Hours',
                                      help="Provide the min hours value for \
                                      check in, checkout days, whatever the \
                                      hours will be provided here based on \
                                      that extra days will be calculated.")
    
class ShooterTeam(models.Model):
    _name = 'paintball.shooter_team'
    _description = 'Paintball Shooter Team'
    
    name = fields.Char(string='Team Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True,  default='draft')
    user_id = fields.Many2one(
        'res.users', string='Salesperson', index=True,  default=lambda self: self.env.user)
    partner_id = fields.Many2one(
        'res.partner', string='Team Leader', readonly=True,
        states={'draft': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    shooter_ids = fields.Many2many('res.partner', 'paintball_shooter_team_res_partner_rel', 'shooter_team_id', 'partner_id', string='Shooter', readonly=True, states={'draft': [('readonly', False)]})
    folio_id = fields.Many2one('paintball.folio', string = 'Folio', readonly=True, states={'draft': [('readonly', False)]})
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('paintball.shooter_team') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('paintball.shooter_team') or _('New')
        result = super(ShooterTeam, self).create(vals)
        return result
    

    


class AccountMove(models.Model):

    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        if self._context.get('folio_id'):
            folio = self.env['paintball.folio'].browse(self._context['folio_id'])
            folio.write({'paintball_invoice_id': res.id,
                         'invoice_status': 'invoiced'})
        return res
    

         
    
    
# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt
from odoo.exceptions import ValidationError, UserError
import pytz


class PaintballFolio(models.Model):

    _inherit = 'paintball.folio'
    _order = 'reservation_id desc'

    reservation_id = fields.Many2one('paintball.reservation',
                                     string='Reservation Id')


    def write(self, vals):
        context = dict(self._context)
        if not context:
            context = {}
        context.update({'from_reservation': True})
        res = super(PaintballFolio, self).write(vals)
        reservation_line_obj = self.env['paintball.zone.reservation.line']
        for folio_obj in self:
            if folio_obj.reservation_id:
                for reservation in folio_obj.reservation_id:
                    reservation_obj = (reservation_line_obj.search
                                       ([('reservation_id', '=',
                                          reservation.id)]))
                    if len(reservation_obj) == 1:
                        for line_id in reservation.reservation_line:
                            line_id = line_id.reserve
                            for zone_id in line_id:
                                vals = {'zone_id': zone_id.id,
                                        'check_in': folio_obj.checkin_date,
                                        'check_out': folio_obj.checkout_date,
                                        'state': 'assigned',
                                        'reservation_id': reservation.id,
                                        }
                                reservation_obj.write(vals)
        return res


class PaintballFolioLineExt(models.Model):

    _inherit = 'paintball.folio.line'

    @api.onchange('checkin_date', 'checkout_date')
    def on_change_checkout(self):
        res = super(PaintballFolioLineExt, self).on_change_checkout()
        paintball_zone_obj = self.env['paintball.zone']
        avail_prod_ids = []
        paintball_zone_ids = paintball_zone_obj.search([])
        for zone in paintball_zone_ids:
            assigned = False
            for line in zone.zone_reservation_line_ids:
                if line.status != 'cancel':
                    if(self.checkin_date <= line.check_in <=
                        self.checkout_date) or (self.checkin_date <=
                                                line.check_out <=
                                                self.checkout_date):
                        assigned = True
                    elif(line.check_in <= self.checkin_date <=
                         line.check_out) or (line.check_in <=
                                             self.checkout_date <=
                                             line.check_out):
                        assigned = True
            if not assigned:
                avail_prod_ids.append(zone.product_id.id)
        return res


    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        Update Paintball Zone Reservation line history"""
        reservation_line_obj = self.env['paintball.zone.reservation.line']
        zone_obj = self.env['paintball.zone']
        prod_id = vals.get('product_id') or self.product_id.id
        chkin = vals.get('checkin_date') or self.checkin_date
        chkout = vals.get('checkout_date') or self.checkout_date
        is_reserved = self.is_reserved
        if prod_id and is_reserved:
            prod_domain = [('product_id', '=', prod_id)]
            prod_zone = zone_obj.search(prod_domain, limit=1)
            if (self.product_id and self.checkin_date and self.checkout_date):
                old_prd_domain = [('product_id', '=', self.product_id.id)]
                old_prod_zone = zone_obj.search(old_prd_domain, limit=1)
                if prod_zone and old_prod_zone:
                    # Check for existing zone lines.
                    srch_rmline = [('zone_id', '=', old_prod_zone.id),
                                   ('check_in', '=', self.checkin_date),
                                   ('check_out', '=', self.checkout_date),
                                   ]
                    rm_lines = reservation_line_obj.search(srch_rmline)
                    if rm_lines:
                        rm_line_vals = {'zone_id': prod_zone.id,
                                        'check_in': chkin,
                                        'check_out': chkout}
                        rm_lines.write(rm_line_vals)
        return super(PaintballFolioLineExt, self).write(vals)


class PaintballReservation(models.Model):

    _name = "paintball.reservation"
    _rec_name = "reservation_no"
    _description = "Reservation"
    _order = 'reservation_no desc'
    _inherit = ['mail.thread']

    reservation_no = fields.Char('Reservation No', readonly=True)
    date_order = fields.Datetime('Date Ordered', readonly=True, required=True,
                                 index=True,
                                 default=(lambda *a: time.strftime(dt)))
    warehouse_id = fields.Many2one('stock.warehouse', 'Paintball', readonly=True,
                                   index=True,
                                   required=True, default=1,
                                   states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', 'Guest Name', readonly=True,
                                 index=True,
                                 required=True,
                                 states={'draft': [('readonly', False)]})
    pricelist_id = fields.Many2one('product.pricelist', 'Scheme',
                                   required=True, readonly=True,
                                   states={'draft': [('readonly', False)]},
                                   help="Pricelist for current reservation.")
    partner_invoice_id = fields.Many2one('res.partner', 'Invoice Address',
                                         readonly=True,
                                         states={'draft':
                                                 [('readonly', False)]},
                                         help="Invoice address for "
                                         "current reservation.")
    partner_order_id = fields.Many2one('res.partner', 'Ordering Contact',
                                       readonly=True,
                                       states={'draft':
                                               [('readonly', False)]},
                                       help="The name and address of the "
                                       "contact that requested the order "
                                       "or quotation.")
    partner_shipping_id = fields.Many2one('res.partner', 'Delivery Address',
                                          readonly=True,
                                          states={'draft':
                                                  [('readonly', False)]},
                                          help="Delivery address"
                                          "for current reservation. ")
    checkin = fields.Datetime('Expected-Date-Arrival', required=True,
                              readonly=True,
                              states={'draft': [('readonly', False)]})
    checkout = fields.Datetime('Expected-Date-Departure', required=True,
                               readonly=True,
                               states={'draft': [('readonly', False)]})
    adults = fields.Integer('Adults', readonly=True,
                            states={'draft': [('readonly', False)]},
                            help='List of adults there in guest list. ')
    children = fields.Integer('Children', readonly=True,
                              states={'draft': [('readonly', False)]},
                              help='Number of children there in guest list.')
    reservation_line = fields.One2many('paintball_reservation.line', 'line_id',
                                       'Reservation Line',
                                       help='Paintball zone reservation details.',
                                       readonly=True,
                                       states={'draft': [('readonly', False)]},
                                       )
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
                              ('cancel', 'Cancel'), ('done', 'Done')],
                             'State', readonly=True,
                             default=lambda *a: 'draft')
    folio_id = fields.Many2many('paintball.folio', 'paintball_folio_reservation_rel',
                                'order_id', 'invoice_id', string='Folio')
    no_of_folio = fields.Integer('No. Folio', compute="_compute_folio_id")
    dummy = fields.Datetime('Dummy')

    def _compute_folio_id(self):
        folio_list = []
        for res in self:
            for folio in res.folio_id:
                folio_list.append(folio.id)
            folio_len = len(folio_list)
            res.no_of_folio = folio_len
        return folio_len

    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        for reserv_rec in self:
            if reserv_rec.state != 'draft':
                raise ValidationError(_('You cannot delete Reservation in %s\
                                         state.') % (reserv_rec.state))
        return super(PaintballReservation, self).unlink()


    def copy(self):
        ctx = dict(self._context) or {}
        ctx.update({'duplicate': True})
        return super(PaintballReservation, self.with_context(ctx)).copy()

    @api.constrains('reservation_line', 'adults', 'children')
    def check_reservation_zones(self):
        '''
        This method is used to validate the reservation_line.
        -----------------------------------------------------
        @param self: object pointer
        @return: raise a warning depending on the validation
        '''
        ctx = dict(self._context) or {}
        for reservation in self:
            cap = 0
            for rec in reservation.reservation_line:
                if len(rec.reserve) == 0:
                    raise ValidationError(_(
                        'Please Select Zones For Reservation.'))
                for zone in rec.reserve:
                    cap += zone.capacity
            if not ctx.get('duplicate'):
                if (reservation.adults + reservation.children) > cap:
                    raise ValidationError(_(
                        'Zone Capacity Exceeded \n'
                        ' Please Select Zones According to'
                        ' Members Accomodation.'))
            if reservation.adults <= 0:
                raise ValidationError(_('Adults must be more than 0'))

    @api.constrains('checkin', 'checkout')
    def check_in_out_dates(self):
        """
        When date_order is less then check-in date or
        Checkout date should be greater than the check-in date.
        """
        if self.checkout and self.checkin:
            if self.checkin < self.date_order:
                raise ValidationError(_('Check-in date should be greater than \
                                         the current date.'))
            if self.checkout < self.checkin:
                raise ValidationError(_('Check-out date should be greater \
                                         than Check-in date.'))

    @api.model
    def _needaction_count(self, domain=None):
        """
         Show a count of draft state reservations on the menu badge.
         """
        return self.search_count([('state', '=', 'draft')])

    @api.onchange('checkout', 'checkin')
    def on_change_checkout(self):
        '''
        When you change checkout or checkin update dummy field
        -----------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        checkout_date = time.strftime(dt)
        checkin_date = time.strftime(dt)
        if not (checkout_date and checkin_date):
            return {'value': {}}
        delta = timedelta(days=1)
        dat_a = time.strptime(checkout_date, dt)[:5]
        addDays = datetime(*dat_a) + delta
        self.dummy = addDays.strftime(dt)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        '''
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the paintball reservation as well
        ---------------------------------------------------------------------
        @param self: object pointer
        '''
        if not self.partner_id:
            self.partner_invoice_id = False
            self.partner_shipping_id = False
            self.partner_order_id = False
        else:
            addr = self.partner_id.address_get(['delivery', 'invoice',
                                                'contact'])
            self.partner_invoice_id = addr['invoice']
            self.partner_order_id = addr['contact']
            self.partner_shipping_id = addr['delivery']
            self.pricelist_id = self.partner_id.property_product_pricelist.id

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if not vals:
            vals = {}
        vals['reservation_no'] = self.env['ir.sequence'].\
            next_by_code('paintball.reservation') or 'New'
        return super(PaintballReservation, self).create(vals)

    def check_overlap(self, date1, date2):
        date2 = datetime.strptime(date2, '%Y-%m-%d')
        date1 = datetime.strptime(date1, '%Y-%m-%d')
        delta = date2 - date1
        return set([date1 + timedelta(days=i) for i in range(delta.days + 1)])

    def confirmed_reservation(self):
        """
        This method create a new record set for paintball zone reservation line
        -------------------------------------------------------------------
        @param self: The object pointer
        @return: new record set for paintball zone reservation line.
        """
        reservation_line_obj = self.env['paintball.zone.reservation.line']
        vals = {}
        for reservation in self:
            reserv_checkin = reservation.checkin
            reserv_checkout = reservation.checkout
            zone_bool = False
            for line_id in reservation.reservation_line:
                for zone_id in line_id.reserve:
                    if zone_id.zone_reservation_line_ids:
                        for reserv in zone_id.zone_reservation_line_ids.\
                                search([('status', 'in', ('confirm', 'done')),
                                        ('zone_id', '=', zone_id.id)]):
                            check_in = reserv.check_in
                            check_out = reserv.check_out
                            if check_in <= reserv_checkin <= check_out:
                                zone_bool = True
                            if check_in <= reserv_checkout <= check_out:
                                zone_bool = True
                            if reserv_checkin <= check_in and \
                                    reserv_checkout >= check_out:
                                zone_bool = True
                            mytime = "%Y-%m-%d"
                            r_checkin = (reservation.checkin).date()
                            r_checkin = r_checkin.strftime(mytime)
                            r_checkout = (reservation.checkout).date()
                            r_checkout = r_checkout.strftime(mytime)
                            check_intm = (reserv.check_in).date()
                            check_outtm = (reserv.check_out).date()
                            check_intm = check_intm.strftime(mytime)
                            check_outtm = check_outtm.strftime(mytime)
                            range1 = [r_checkin, r_checkout]
                            range2 = [check_intm, check_outtm]
                            overlap_dates = self.check_overlap(*range1) \
                                & self.check_overlap(*range2)
                            overlap_dates = [datetime.strftime(dates,
                                                               '%d/%m/%Y') for
                                             dates in overlap_dates]
                            if zone_bool:
                                raise ValidationError(_('You tried to Confirm '
                                                        'Reservation with zone'
                                                        ' those already '
                                                        'reserved in this '
                                                        'Reservation Period. '
                                                        'Overlap Dates are '
                                                        '%s') % overlap_dates)
                            else:
                                self.state = 'confirm'
                                vals = {'zone_id': zone_id.id,
                                        'check_in': reservation.checkin,
                                        'check_out': reservation.checkout,
                                        'state': 'assigned',
                                        'reservation_id': reservation.id,
                                        }
                                zone_id.write({'iszone': False,
                                               'status': 'occupied'})
                        else:
                            self.state = 'confirm'
                            vals = {'zone_id': zone_id.id,
                                    'check_in': reservation.checkin,
                                    'check_out': reservation.checkout,
                                    'state': 'assigned',
                                    'reservation_id': reservation.id,
                                    }
                            zone_id.write({'iszone': False,
                                           'status': 'occupied'})
                    else:
                        self.state = 'confirm'
                        vals = {'zone_id': zone_id.id,
                                'check_in': reservation.checkin,
                                'check_out': reservation.checkout,
                                'state': 'assigned',
                                'reservation_id': reservation.id,
                                }
                        zone_id.write({'iszone': False,
                                       'status': 'occupied'})
                    reservation_line_obj.create(vals)
        return True

    def cancel_reservation(self):
        """
        This method cancel record set for paintball zone reservation line
        ------------------------------------------------------------------
        @param self: The object pointer
        @return: cancel record set for paintball zone reservation line.
        """
        zone_res_line_obj = self.env['paintball.zone.reservation.line']
        paintball_res_line_obj = self.env['paintball_reservation.line']
        self.state = 'cancel'
        zone_reservation_line = zone_res_line_obj.search([('reservation_id',
                                                           'in', self.ids)])
        zone_reservation_line.write({'state': 'unassigned'})
        zone_reservation_line.unlink()
        reservation_lines = paintball_res_line_obj.search([('line_id',
                                                        'in', self.ids)])
        for reservation_line in reservation_lines:
            reservation_line.reserve.write({'iszone': True,
                                            'status': 'available'})
        return True


    def set_to_draft_reservation(self):
        self.state = 'draft'
        return True

    def action_send_reservation_mail(self):
        '''
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        '''
        assert len(self._ids) == 1, 'This is for a single id at a time.'
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = (ir_model_data.get_object_reference
                           ('paintball_reservation',
                            'email_template_paintball_reservation')[1])
        except ValueError:
            template_id = False
        try:
            compose_form_id = (ir_model_data.get_object_reference
                               ('mail',
                                'email_compose_message_wizard_form')[1])
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'paintball.reservation',
            'default_res_id': self._ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_send': True,
            'mark_so_as_sent': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
            'force_send': True
        }

    @api.model
    def reservation_reminder_24hrs(self):
        """
        This method is for scheduler
        every 1day scheduler will call this method to
        find all tomorrow's reservations.
        ----------------------------------------------
        @param self: The object pointer
        @return: send a mail
        """
        now_str = time.strftime(dt)
        now_date = datetime.strptime(now_str, dt)
        ir_model_data = self.env['ir.model.data']
        template_id = (ir_model_data.get_object_reference
                       ('paintball_reservation',
                        'mail_template_reservation_reminder_24hrs')[1])
        template_rec = self.env['mail.template'].browse(template_id)
        for reserv_rec in self.search([]):
            checkin_date = reserv_rec.checkin
            difference = relativedelta(now_date, checkin_date)
            if(difference.days == -1 and reserv_rec.partner_id.email and
               reserv_rec.state == 'confirm'):
                template_rec.send_mail(reserv_rec.id, force_send=True)
        return True


    def create_folio(self):
        """
        This method is for create new paintball folio.
        -----------------------------------------
        @param self: The object pointer
        @return: new record set for paintball folio.
        """
        paintball_folio_obj = self.env['paintball.folio']
        zone_obj = self.env['paintball.zone']
        for reservation in self:
            folio_lines = []
            checkin_date = reservation['checkin']
            checkout_date = reservation['checkout']
            if not self.checkin < self.checkout:
                raise ValidationError(_('Checkout date should be greater \
                                         than the Check-in date.'))
            duration_vals = (self.onchange_check_dates
                             (checkin_date=checkin_date,
                              checkout_date=checkout_date, duration=False))
            duration = duration_vals.get('duration') or 0.0
            folio_vals = {
                'date_order': reservation.date_order,
                'warehouse_id': reservation.warehouse_id.id,
                'partner_id': reservation.partner_id.id,
                'pricelist_id': reservation.pricelist_id.id,
                'partner_invoice_id': reservation.partner_invoice_id.id,
                'partner_shipping_id': reservation.partner_shipping_id.id,
                'checkin_date': reservation.checkin,
                'checkout_date': reservation.checkout,
                'duration': duration,
                'reservation_id': reservation.id,
                'service_lines': reservation['folio_id']
            }
            for line in reservation.reservation_line:
                for r in line.reserve:
                    folio_lines.append((0, 0, {
                        'checkin_date': checkin_date,
                        'checkout_date': checkout_date,
                        'product_id': r.product_id and r.product_id.id,
                        'name': reservation['reservation_no'],
                        'price_unit': r.list_price,
                        'product_uom_qty': duration,
                        'is_reserved': True}))
                    res_obj = zone_obj.browse([r.id])
                    res_obj.write({'status': 'occupied', 'iszone': False})
            folio_vals.update({'zone_lines': folio_lines})
            folio = paintball_folio_obj.create(folio_vals)
            if folio:
                for rm_line in folio.zone_lines:
                    rm_line.product_id_change()
            self._cr.execute('insert into paintball_folio_reservation_rel'
                             '(order_id, invoice_id) values (%s,%s)',
                             (reservation.id, folio.id))
            self.state = 'done'
        return True


    def onchange_check_dates(self, checkin_date=False, checkout_date=False,
                             duration=False):
        '''
        This method gives the duration between check in checkout if
        customer will leave only for some hour it would be considers
        as a whole day. If customer will checkin checkout for more or equal
        hours, which configured in company as additional hours than it would
        be consider as full days
        --------------------------------------------------------------------
        @param self: object pointer
        @return: Duration and checkout_date
        '''
        value = {}
        configured_addition_hours = 0
        wc_id = self.warehouse_id
        whcomp_id = wc_id or wc_id.company_id
        if whcomp_id:
            configured_addition_hours = wc_id.company_id.additional_hours
        duration = 0
        if checkin_date and checkout_date:
            dur = checkout_date - checkin_date
            duration = dur.days + 1
            if configured_addition_hours > 0:
                additional_hours = abs((dur.seconds / 60))
                if additional_hours <= abs(configured_addition_hours * 60):
                    duration -= 1
        value.update({'duration': duration})
        return value


class PaintballReservationLine(models.Model):

    _name = "paintball_reservation.line"
    _description = "Reservation Line"

    name = fields.Char('Name')
    line_id = fields.Many2one('paintball.reservation')
    reserve = fields.Many2many('paintball.zone',
                               'paintball_reservation_line_zone_rel',
                               'paintball_reservation_line_id', 'zone_id',
                               domain="[('iszone','=',True),\
                               ('categ_id','=',categ_id)]")
    categ_id = fields.Many2one('paintball.zone.type', 'Zone Type')

    @api.onchange('categ_id')
    def on_change_categ(self):
        '''
        When you change categ_id it check checkin and checkout are
        filled or not if not then raise warning
        -----------------------------------------------------------
        @param self: object pointer
        '''
        paintball_zone_obj = self.env['paintball.zone']
        paintball_zone_ids = paintball_zone_obj.search([('categ_id', '=',
                                                 self.categ_id.id)])
        zone_ids = []
        if not self.line_id.checkin:
            raise ValidationError(_('Before choosing a zone,\n You have to \
                                     select a Check in date or a Check out \
                                     date in the reservation form.'))
        for zone in paintball_zone_ids:
            assigned = False
            for line in zone.zone_reservation_line_ids:
                if line.status != 'cancel':
                    if(self.line_id.checkin <= line.check_in <=
                        self.line_id.checkout) or (self.line_id.checkin <=
                                                   line.check_out <=
                                                   self.line_id.checkout):
                        assigned = True
                    elif(line.check_in <= self.line_id.checkin <=
                         line.check_out) or (line.check_in <=
                                             self.line_id.checkout <=
                                             line.check_out):
                        assigned = True
            for rm_line in zone.zone_line_ids:
                if rm_line.status != 'cancel':
                    if(self.line_id.checkin <= rm_line.check_in <=
                       self.line_id.checkout) or (self.line_id.checkin <=
                                                  rm_line.check_out <=
                                                  self.line_id.checkout):
                        assigned = True
                    elif(rm_line.check_in <= self.line_id.checkin <=
                         rm_line.check_out) or (rm_line.check_in <=
                                                self.line_id.checkout <=
                                                rm_line.check_out):
                        assigned = True
            if not assigned:
                zone_ids.append(zone.id)
        domain = {'reserve': [('id', 'in', zone_ids)]}
        return {'domain': domain}


    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        paintball_zone_reserv_line_obj = self.env['paintball.zone.reservation.line']
        for reserv_rec in self:
            for rec in reserv_rec.reserve:
                hres_arg = [('zone_id', '=', rec.id),
                            ('reservation_id', '=', reserv_rec.line_id.id)]
                myobj = paintball_zone_reserv_line_obj.search(hres_arg)
                if myobj.ids:
                    rec.write({'iszone': True, 'status': 'available'})
                    myobj.unlink()
        return super(PaintballReservationLine, self).unlink()


class PaintballZoneReservationLine(models.Model):

    _name = 'paintball.zone.reservation.line'
    _description = 'Paintball Zone Reservation'
    _rec_name = 'zone_id'

    zone_id = fields.Many2one('paintball.zone', string='Zone id')
    check_in = fields.Datetime('Check In Date', required=True)
    check_out = fields.Datetime('Check Out Date', required=True)
    state = fields.Selection([('assigned', 'Assigned'),
                              ('unassigned', 'Unassigned')], 'Zone Status')
    reservation_id = fields.Many2one('paintball.reservation',
                                     string='Reservation')
    status = fields.Selection(string='state', related='reservation_id.state')


class PaintballZone(models.Model):

    _inherit = 'paintball.zone'
    _description = 'Paintball Zone'

    zone_reservation_line_ids = fields.One2many('paintball.zone.reservation.line',
                                                'zone_id',
                                                string='Zone Reserve Line')


    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        for zone in self:
            for reserv_line in zone.zone_reservation_line_ids:
                if reserv_line.status == 'confirm':
                    raise ValidationError(_('User is not able to delete the \
                                            zone after the zone in %s state \
                                            in reservation')
                                          % (reserv_line.status))
        return super(PaintballZone, self).unlink()

    @api.model
    def cron_zone_line(self):
        """
        This method is for scheduler
        every 1min scheduler will call this method and check Status of
        zone is occupied or available
        --------------------------------------------------------------
        @param self: The object pointer
        @return: update status of paintball zone reservation line
        """
        reservation_line_obj = self.env['paintball.zone.reservation.line']
        folio_zone_line_obj = self.env['folio.zone.line']
        now = datetime.now()
        curr_date = now.strftime(dt)
        for zone in self.search([]):
            reserv_line_ids = [reservation_line.id for
                               reservation_line in
                               zone.zone_reservation_line_ids]
            reserv_args = [('id', 'in', reserv_line_ids),
                           ('check_in', '<=', curr_date),
                           ('check_out', '>=', curr_date)]
            reservation_line_ids = reservation_line_obj.search(reserv_args)
            zones_ids = [zone_line.ids for zone_line in zone.zone_line_ids]
            rom_args = [('id', 'in', zones_ids),
                        ('check_in', '<=', curr_date),
                        ('check_out', '>=', curr_date)]
            zone_line_ids = folio_zone_line_obj.search(rom_args)
            status = {'iszone': True, 'color': 5}
            if reservation_line_ids.ids:
                status = {'iszone': False, 'color': 2}
            zone.write(status)
            if zone_line_ids.ids:
                status = {'iszone': False, 'color': 2}
            zone.write(status)
            if reservation_line_ids.ids and zone_line_ids.ids:
                raise ValidationError(_('Please Check Zones Status \
                                         for %s.' % (zone.name)))
        return True


class ZoneReservationSummary(models.Model):

    _name = 'zone.reservation.summary'
    _description = 'Zone reservation summary'

    name = fields.Char('Reservation Summary', default='Reservations Summary',
                       invisible=True)
    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date To')
    summary_header = fields.Text('Summary Header')
    zone_summary = fields.Text('Zone Summary')

    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        if self._context is None:
            self._context = {}
        res = super(ZoneReservationSummary, self).default_get(fields)
        # Added default datetime as today and date to as today + 30.
        from_dt = datetime.today()
        dt_from = from_dt.strftime(dt)
        to_dt = from_dt + relativedelta(days=30)
        dt_to = to_dt.strftime(dt)
        res.update({'date_from': dt_from, 'date_to': dt_to})

        if not self.date_from and self.date_to:
            date_today = datetime.datetime.today()
            first_day = datetime.datetime(date_today.year,
                                          date_today.month, 1, 0, 0, 0)
            first_temp_day = first_day + relativedelta(months=1)
            last_temp_day = first_temp_day - relativedelta(days=1)
            last_day = datetime.datetime(last_temp_day.year,
                                         last_temp_day.month,
                                         last_temp_day.day, 23, 59, 59)
            date_froms = first_day.strftime(dt)
            date_ends = last_day.strftime(dt)
            res.update({'date_from': date_froms, 'date_to': date_ends})
        return res


    def zone_reservation(self):
        '''
        @param self: object pointer
        '''
        mod_obj = self.env['ir.model.data']
        if self._context is None:
            self._context = {}
        model_data_ids = mod_obj.search([('model', '=', 'ir.ui.view'),
                                         ('name', '=',
                                          'view_paintball_reservation_form')])
        resource_id = model_data_ids.read(fields=['res_id'])[0]['res_id']
        return {'name': _('Reconcile Write-Off'),
                'context': self._context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'paintball.reservation',
                'views': [(resource_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
                }

    @api.onchange('date_from', 'date_to')
    def get_zone_summary(self):
        '''
        @param self: object pointer
         '''
        res = {}
        all_detail = []
        zone_obj = self.env['paintball.zone']
        reservation_line_obj = self.env['paintball.zone.reservation.line']
        folio_zone_line_obj = self.env['folio.zone.line']
        user_obj = self.env['res.users']
        date_range_list = []
        main_header = []
        summary_header_list = ['Zones']
        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                raise UserError(_('Please Check Time period Date From can\'t \
                                   be greater than Date To !'))
            if self._context.get('tz', False):
                timezone = pytz.timezone(self._context.get('tz', False))
            else:
                timezone = pytz.timezone('UTC')
            d_frm_obj = (self.date_from).replace(tzinfo=pytz.timezone('UTC')
                                                 ).astimezone(timezone)
            d_to_obj = (self.date_to).replace(tzinfo=pytz.timezone('UTC')
                                              ).astimezone(timezone)
            temp_date = d_frm_obj
            while(temp_date <= d_to_obj):
                val = ''
                val = (str(temp_date.strftime("%a")) + ' ' +
                       str(temp_date.strftime("%b")) + ' ' +
                       str(temp_date.strftime("%d")))
                summary_header_list.append(val)
                date_range_list.append(temp_date.strftime
                                       (dt))
                temp_date = temp_date + timedelta(days=1)
            all_detail.append(summary_header_list)
            zone_ids = zone_obj.search([])
            all_zone_detail = []
            for zone in zone_ids:
                zone_detail = {}
                zone_list_stats = []
                zone_detail.update({'name': zone.name or ''})
                if not zone.zone_reservation_line_ids and \
                   not zone.zone_line_ids:
                    for chk_date in date_range_list:
                        zone_list_stats.append({'state': 'Free',
                                                'date': chk_date,
                                                'zone_id': zone.id})
                else:
                    for chk_date in date_range_list:
                        ch_dt = chk_date[:10] + ' 23:59:59'
                        ttime = datetime.strptime(ch_dt, dt)
                        c = ttime.replace(tzinfo=timezone).\
                            astimezone(pytz.timezone('UTC'))
                        chk_date = c.strftime(dt)
                        reserline_ids = zone.zone_reservation_line_ids.ids
                        reservline_ids = (reservation_line_obj.search
                                          ([('id', 'in', reserline_ids),
                                            ('check_in', '<=', chk_date),
                                            ('check_out', '>=', chk_date),
                                            ('state', '=', 'assigned')
                                            ]))
                        if not reservline_ids:
                            sdt = dt
                            chk_date = datetime.strptime(chk_date, sdt)
                            chk_date = datetime.\
                                strftime(chk_date - timedelta(days=1), sdt)
                            reservline_ids = (reservation_line_obj.search
                                              ([('id', 'in', reserline_ids),
                                                ('check_in', '<=', chk_date),
                                                ('check_out', '>=', chk_date),
                                                ('state', '=', 'assigned')]))
                            for res_zone in reservline_ids:
                                cid = res_zone.check_in
                                cod = res_zone.check_out
                                dur = cod - cid
                                if zone_list_stats:
                                    count = 0
                                    for rlist in zone_list_stats:
                                        cidst = datetime.strftime(cid, dt)
                                        codst = datetime.strftime(cod, dt)
                                        rm_id = res_zone.zone_id.id
                                        ci = rlist.get('date') >= cidst
                                        co = rlist.get('date') <= codst
                                        rm = rlist.get('zone_id') == rm_id
                                        st = rlist.get('state') == 'Reserved'
                                        if ci and co and rm and st:
                                            count += 1
                                    if count - dur.days == 0:
                                        c_id1 = user_obj.browse(self._uid)
                                        c_id = c_id1.company_id
                                        con_add = 0
                                        amin = 0.0
                                        if c_id:
                                            con_add = c_id.additional_hours
#                                        When configured_addition_hours is
#                                        greater than zero then we calculate
#                                        additional minutes
                                        if con_add > 0:
                                            amin = abs(con_add * 60)
                                        hr_dur = abs((dur.seconds / 60))
#                                        When additional minutes is greater
#                                        than zero then check duration with
#                                        extra minutes and give the zone
#                                        reservation status is reserved or
#                                        free
                                        if amin > 0:
                                            if hr_dur >= amin:
                                                reservline_ids = True
                                            else:
                                                reservline_ids = False
                                        else:
                                            if hr_dur > 0:
                                                reservline_ids = True
                                            else:
                                                reservline_ids = False
                                    else:
                                        reservline_ids = False
                        fol_zone_line_ids = zone.zone_line_ids.ids
                        chk_state = ['draft', 'cancel']
                        folio_resrv_ids = (folio_zone_line_obj.search
                                           ([('id', 'in', fol_zone_line_ids),
                                             ('check_in', '<=', chk_date),
                                             ('check_out', '>=', chk_date),
                                             ('status', 'not in', chk_state)
                                             ]))
                        if reservline_ids or folio_resrv_ids:
                            zone_list_stats.append({'state': 'Reserved',
                                                    'date': chk_date,
                                                    'zone_id': zone.id,
                                                    'is_draft': 'No',
                                                    'data_model': '',
                                                    'data_id': 0})
                        else:
                            zone_list_stats.append({'state': 'Free',
                                                    'date': chk_date,
                                                    'zone_id': zone.id})

                zone_detail.update({'value': zone_list_stats})
                all_zone_detail.append(zone_detail)
            main_header.append({'header': summary_header_list})
            self.summary_header = str(main_header)
            self.zone_summary = str(all_zone_detail)
        return res


class QuickZoneReservation(models.TransientModel):
    _name = 'quick.zone.reservation'
    _description = 'Quick Zone Reservation'

    partner_id = fields.Many2one('res.partner', string="Customer",
                                 required=True)
    check_in = fields.Datetime('Check In', required=True)
    check_out = fields.Datetime('Check Out', required=True)
    zone_id = fields.Many2one('paintball.zone', 'Zone', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Paintball', required=True)
    pricelist_id = fields.Many2one('product.pricelist', 'pricelist')
    partner_invoice_id = fields.Many2one('res.partner', 'Invoice Address',
                                         required=True)
    partner_order_id = fields.Many2one('res.partner', 'Ordering Contact',
                                       required=True)
    partner_shipping_id = fields.Many2one('res.partner', 'Delivery Address',
                                          required=True)
    adults = fields.Integer('Adults', size=64)

    @api.onchange('check_out', 'check_in')
    def on_change_check_out(self):
        '''
        When you change checkout or checkin it will check whether
        Checkout date should be greater than Checkin date
        and update dummy field
        -----------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        if self.check_out and self.check_in:
            if self.check_out < self.check_in:
                raise ValidationError(_('Checkout date should be greater \
                                         than Checkin date.'))

    @api.onchange('partner_id')
    def onchange_partner_id_res(self):
        '''
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the paintball reservation as well
        ---------------------------------------------------------------------
        @param self: object pointer
        '''
        if not self.partner_id:
            self.partner_invoice_id = False
            self.partner_shipping_id = False
            self.partner_order_id = False
        else:
            addr = self.partner_id.address_get(['delivery', 'invoice',
                                                'contact'])
            self.partner_invoice_id = addr['invoice']
            self.partner_order_id = addr['contact']
            self.partner_shipping_id = addr['delivery']
            self.pricelist_id = self.partner_id.property_product_pricelist.id

    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        if self._context is None:
            self._context = {}
        res = super(QuickZoneReservation, self).default_get(fields)
        if self._context:
            keys = self._context.keys()
            if 'date' in keys:
                res.update({'check_in': self._context['date']})
            if 'zone_id' in keys:
                zoneid = self._context['zone_id']
                res.update({'zone_id': int(zoneid)})
        return res


    def zone_reserve(self):
        """
        This method create a new record for paintball.reservation
        -----------------------------------------------------
        @param self: The object pointer
        @return: new record set for paintball reservation.
        """
        paintball_res_obj = self.env['paintball.reservation']
        for res in self:
            rec = (paintball_res_obj.create
                   ({'partner_id': res.partner_id.id,
                     'partner_invoice_id': res.partner_invoice_id.id,
                     'partner_order_id': res.partner_order_id.id,
                     'partner_shipping_id': res.partner_shipping_id.id,
                     'checkin': res.check_in,
                     'checkout': res.check_out,
                     'warehouse_id': res.warehouse_id.id,
                     'pricelist_id': res.pricelist_id.id,
                     'adults': res.adults,
                     'reservation_line': [(0, 0,
                                           {'reserve': [(6, 0,
                                                         [res.zone_id.id])],
                                            'name': (res.zone_id and
                                                     res.zone_id.name or '')
                                            })]
                     }))
        return rec
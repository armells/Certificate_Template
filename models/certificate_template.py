from odoo import models, fields

class SurveyCertificateTemplate(models.Model):
    _name = 'survey.certificate.template'
    _description = 'Survey Certificate Template'

    name = fields.Char("Template Name", required=True)
    file = fields.Binary("Template File", required=True)
    filename = fields.Char("Filename")
    active = fields.Boolean(default=True)
    
    # Pengaturan posisi NAMA
    name_position_y = fields.Integer(
        "Name Position Y (%)", 
        default=45, 
        help="Posisi vertikal nama dari atas (0-100%)"
    )
    name_font_size = fields.Integer("Name Font Size", default=60)
    name_color = fields.Char("Name Text Color", default="#000000", help="Hex color code (e.g., #000000)")
    
    # Pengaturan posisi TANGGAL
    show_date = fields.Boolean("Show Date", default=True)
    date_position_offset = fields.Integer(
        "Date Position (offset from name)", 
        default=100, 
        help="Jarak tanggal dari nama dalam pixel"
    )
    date_font_size = fields.Integer("Date Font Size", default=30)
    date_color = fields.Char("Date Text Color", default="#000000")
    
    # Pengaturan LOGO
    show_logo = fields.Boolean("Show Logo", default=False)
    logo_image = fields.Binary("Logo Image")
    logo_position_x = fields.Integer("Logo Position X (%)", default=10, help="0-100%")
    logo_position_y = fields.Integer("Logo Position Y (%)", default=10, help="0-100%")
    logo_width = fields.Integer("Logo Width (px)", default=150)
    
    # Pengaturan TANDA TANGAN
    show_signature = fields.Boolean("Show Signature", default=False)
    signature_image = fields.Binary("Signature Image")
    signature_position_x = fields.Integer("Signature Position X (%)", default=50, help="0-100%")
    signature_position_y = fields.Integer("Signature Position Y (%)", default=75, help="0-100%")
    signature_width = fields.Integer("Signature Width (px)", default=200)
    signature_label = fields.Char("Signature Label", default="Manager", help="Text di bawah signature")

from odoo import models, fields

class SurveyCertificateTemplate(models.Model):
    _name = 'survey.certificate.template'
    _description = 'Survey Certificate Template'

    name = fields.Char("Template Name", required=True)
    file = fields.Binary("Template File", required=True)
    filename = fields.Char("Filename")
    active = fields.Boolean(default=True)

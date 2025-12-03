from odoo import models, fields, api
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import logging

_logger = logging.getLogger(__name__)

class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    certificate_template_id = fields.Many2one(
        'survey.certificate.template',
        string='Certificate Template',
        help='Select certificate template for this survey'
    )


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    certification_report_image = fields.Binary(
        string='Certification Report Image',
        compute='_compute_certification_report_image',
        store=False
    )

    @api.depends('survey_id.certificate_template_id', 'partner_id', 'email')
    def _compute_certification_report_image(self):
        """Compute certification report image"""
        for record in self:
            if record.survey_id.certificate_template_id:
                _logger.info(f"=== Computing CUSTOM certificate for {record.partner_id.name or record.email} ===")
                record.certification_report_image = record._generate_custom_certificate()
            else:
                try:
                    super(SurveyUserInput, record)._compute_certification_report_image()
                except:
                    record.certification_report_image = False

    def _generate_custom_certificate(self):
        """Generate custom certificate with Pillow"""
        self.ensure_one()
        
        template = self.survey_id.certificate_template_id
        
        if not template or not template.file:
            return False
        
        try:
            _logger.info(f"Generating custom certificate using template: {template.name}")
            
            template_data = base64.b64decode(template.file)
            img = Image.open(BytesIO(template_data))
            
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            draw = ImageDraw.Draw(img)
            
            partner_name = self.partner_id.name if self.partner_id else self.email or "Participant"
            
            font_name = None
            font_date = None
            
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            ]
            
            for font_path in font_paths:
                try:
                    font_name = ImageFont.truetype(font_path, 60)
                    font_date = ImageFont.truetype(font_path.replace("-Bold", ""), 30)
                    break
                except:
                    continue
            
            if not font_name:
                font_name = ImageFont.load_default()
                font_date = ImageFont.load_default()
            
            img_width, img_height = img.size
            
            name_bbox = draw.textbbox((0, 0), partner_name, font=font_name)
            name_width = name_bbox[2] - name_bbox[0]
            name_x = (img_width - name_width) // 2
            name_y = int(img_height * 0.45)
            
            draw.text((name_x, name_y), partner_name, fill='#000000', font=font_name)
            
            completion_date = fields.Date.today().strftime("%B %d, %Y")
            date_bbox = draw.textbbox((0, 0), completion_date, font=font_date)
            date_width = date_bbox[2] - date_bbox[0]
            date_x = (img_width - date_width) // 2
            date_y = name_y + 100
            
            draw.text((date_x, date_y), completion_date, fill='#000000', font=font_date)
            
            output = BytesIO()
            img.save(output, format='PNG')
            output.seek(0)
            
            result = base64.b64encode(output.read())
            _logger.info("=== Custom certificate generated successfully! ===")
            
            return result
            
        except Exception as e:
            _logger.error(f"Error: {str(e)}", exc_info=True)
            return False

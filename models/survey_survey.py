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

    def action_survey_preview_certification_template(self):
        """Override preview button to open in new tab without download"""
        self.ensure_one()
        
        if self.certificate_template_id:
            # Redirect to preview page (image in browser)
            return {
                'type': 'ir.actions.act_url',
                'url': f'/survey/certificate/preview/{self.id}',
                'target': 'new',
            }
        else:
            # Use default preview
            return super().action_survey_preview_certification_template()


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
        """Generate custom certificate with configurable positions"""
        self.ensure_one()
        
        template = self.survey_id.certificate_template_id
        
        if not template or not template.file:
            return False
        
        try:
            _logger.info(f"Generating custom certificate using template: {template.name}")
            
            # Decode template
            template_data = base64.b64decode(template.file)
            img = Image.open(BytesIO(template_data))
            
            # Convert mode
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            draw = ImageDraw.Draw(img)
            img_width, img_height = img.size
            
            # === TAMBAHKAN LOGO ===
            if template.show_logo and template.logo_image:
                try:
                    logo_data = base64.b64decode(template.logo_image)
                    logo = Image.open(BytesIO(logo_data))
                    
                    # Resize logo
                    logo_width = template.logo_width
                    logo_height = int(logo.height * (logo_width / logo.width))
                    logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
                    
                    # Position logo
                    logo_x = int(img_width * (template.logo_position_x / 100))
                    logo_y = int(img_height * (template.logo_position_y / 100))
                    
                    # Paste logo
                    if logo.mode == 'RGBA':
                        img.paste(logo, (logo_x, logo_y), logo)
                    else:
                        img.paste(logo, (logo_x, logo_y))
                        
                    _logger.info(f"Logo added at ({logo_x}, {logo_y})")
                except Exception as e:
                    _logger.error(f"Error adding logo: {e}")
            
            # === TULIS NAMA ===
            partner_name = self.partner_id.name if self.partner_id else self.email or "Participant"
            
            # Load font
            font_name = None
            font_date = None
            
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            ]
            
            for font_path in font_paths:
                try:
                    font_name = ImageFont.truetype(font_path, template.name_font_size)
                    font_date = ImageFont.truetype(font_path.replace("-Bold", ""), template.date_font_size)
                    break
                except:
                    continue
            
            if not font_name:
                font_name = ImageFont.load_default()
                font_date = ImageFont.load_default()
            
            # Posisi nama (center horizontal, vertical sesuai setting)
            name_bbox = draw.textbbox((0, 0), partner_name, font=font_name)
            name_width = name_bbox[2] - name_bbox[0]
            name_x = (img_width - name_width) // 2
            name_y = int(img_height * (template.name_position_y / 100))
            
            draw.text((name_x, name_y), partner_name, fill=template.name_color, font=font_name)
            _logger.info(f"Name '{partner_name}' added at ({name_x}, {name_y})")
            
            # === TULIS TANGGAL ===
            if template.show_date:
                completion_date = fields.Date.today().strftime("%B %d, %Y")
                date_bbox = draw.textbbox((0, 0), completion_date, font=font_date)
                date_width = date_bbox[2] - date_bbox[0]
                date_x = (img_width - date_width) // 2
                date_y = name_y + template.date_position_offset
                
                draw.text((date_x, date_y), completion_date, fill=template.date_color, font=font_date)
                _logger.info(f"Date '{completion_date}' added at ({date_x}, {date_y})")
            
            # === TAMBAHKAN SIGNATURE ===
            if template.show_signature and template.signature_image:
                try:
                    sig_data = base64.b64decode(template.signature_image)
                    signature = Image.open(BytesIO(sig_data))
                    
                    # Resize signature
                    sig_width = template.signature_width
                    sig_height = int(signature.height * (sig_width / signature.width))
                    signature = signature.resize((sig_width, sig_height), Image.Resampling.LANCZOS)
                    
                    # Position signature
                    sig_x = int(img_width * (template.signature_position_x / 100)) - (sig_width // 2)
                    sig_y = int(img_height * (template.signature_position_y / 100))
                    
                    # Paste signature
                    if signature.mode == 'RGBA':
                        img.paste(signature, (sig_x, sig_y), signature)
                    else:
                        img.paste(signature, (sig_x, sig_y))
                    
                    # Tambahkan label signature
                    if template.signature_label:
                        label_bbox = draw.textbbox((0, 0), template.signature_label, font=font_date)
                        label_width = label_bbox[2] - label_bbox[0]
                        label_x = sig_x + (sig_width // 2) - (label_width // 2)
                        label_y = sig_y + sig_height + 10
                        
                        draw.text((label_x, label_y), template.signature_label, fill='#000000', font=font_date)
                    
                    _logger.info(f"Signature added at ({sig_x}, {sig_y})")
                except Exception as e:
                    _logger.error(f"Error adding signature: {e}")
            
            # === OUTPUT ===
            output = BytesIO()
            img.save(output, format='PNG')
            output.seek(0)
            
            result = base64.b64encode(output.read())
            _logger.info("=== Custom certificate generated successfully! ===")
            
            return result
            
        except Exception as e:
            _logger.error(f"Error generating custom certificate: {str(e)}", exc_info=True)
            return False

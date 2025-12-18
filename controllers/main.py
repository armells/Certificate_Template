from odoo import http
from odoo.http import request
import base64
import json
import logging

_logger = logging.getLogger(__name__)


class SurveyCertificateController(http.Controller):

    @http.route('/survey/certificate/preview/<int:survey_id>', type='http', auth='user', website=True)
    def certificate_preview(self, survey_id, **kwargs):
        """Preview certificate in browser without download"""
        
        survey = request.env['survey.survey'].browse(survey_id)
        
        if not survey.exists() or not survey.certification:
            return request.not_found()
        
        fake_user_input = request.env['survey.user_input'].sudo().create({
            'survey_id': survey.id,
            'email': request.env.user.email or 'demo@example.com',
            'partner_id': request.env.user.partner_id.id,
            'test_entry': True,
        })
        
        if survey.certificate_template_id:
            cert_image = fake_user_input.certification_report_image
            
            if cert_image:
                fake_user_input.sudo().unlink()
                
                return request.make_response(
                    base64.b64decode(cert_image),
                    headers=[
                        ('Content-Type', 'image/png'),
                        ('Content-Disposition', 'inline; filename="certificate_preview.png"')
                    ]
                )
        
        report = request.env.ref('survey.certification_report')
        pdf_content, _ = report.sudo()._render_qweb_pdf([fake_user_input.id])
        
        fake_user_input.sudo().unlink()
        
        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'inline; filename="certificate_preview.pdf"')
            ]
        )

    @http.route('/certificate/editor/<int:template_id>', type='http', auth='user', website=True)
    def certificate_editor(self, template_id, **kwargs):
        """Visual certificate editor page"""
        template = request.env['survey.certificate.template'].browse(template_id)
        
        if not template.exists():
            return request.not_found()
        
        return request.render('survey_certificate_template.certificate_editor_page', {
            'template': template,
        })

    @http.route('/certificate/template/image/<int:template_id>', type='http', auth='user')
    def get_template_image(self, template_id, **kwargs):
        """Return template image as binary PNG"""
        template = request.env['survey.certificate.template'].browse(template_id)
        
        if not template.exists() or not template.file:
            _logger.warning(f"Template {template_id} not found or has no file")
            return request.not_found()
        
        try:
            image_data = base64.b64decode(template.file)
            _logger.info(f"Serving template image {template_id}, size: {len(image_data)} bytes")
            
            return request.make_response(
                image_data,
                headers=[
                    ('Content-Type', 'image/png'),
                    ('Cache-Control', 'no-cache'),
                ]
            )
        except Exception as e:
            _logger.error(f"Error decoding template image: {e}", exc_info=True)
            return request.not_found()

    @http.route('/certificate/template/logo/<int:template_id>', type='http', auth='user')
    def get_template_logo(self, template_id, **kwargs):
        """Return logo image as binary PNG"""
        template = request.env['survey.certificate.template'].browse(template_id)
        
        if not template.exists() or not template.logo_image:
            return request.not_found()
        
        try:
            image_data = base64.b64decode(template.logo_image)
            
            return request.make_response(
                image_data,
                headers=[
                    ('Content-Type', 'image/png'),
                    ('Cache-Control', 'no-cache'),
                ]
            )
        except Exception as e:
            _logger.error(f"Error decoding logo image: {e}", exc_info=True)
            return request.not_found()

    @http.route('/certificate/template/signature/<int:template_id>', type='http', auth='user')
    def get_template_signature(self, template_id, **kwargs):
        """Return signature image as binary PNG"""
        template = request.env['survey.certificate.template'].browse(template_id)
        
        if not template.exists() or not template.signature_image:
            return request.not_found()
        
        try:
            image_data = base64.b64decode(template.signature_image)
            
            return request.make_response(
                image_data,
                headers=[
                    ('Content-Type', 'image/png'),
                    ('Cache-Control', 'no-cache'),
                ]
            )
        except Exception as e:
            _logger.error(f"Error decoding signature image: {e}", exc_info=True)
            return request.not_found()

    @http.route('/certificate/editor/save', type='json', auth='user', methods=['POST'])
    def save_editor_layout(self, template_id, layout, **kwargs):
        """Save layout configuration from visual editor"""
        template = request.env['survey.certificate.template'].browse(int(template_id))
        
        if not template.exists():
            return {'success': False, 'error': 'Template not found'}
        
        try:
            _logger.info(f"Saving layout for template {template.id}")
            
            template.write({
                'layout_json': json.dumps(layout)
            })
            
            for obj in layout.get('objects', []):
                if obj['id'] == 'name':
                    template.write({
                        'name_position_y': int((obj['top'] / layout['canvas_height']) * 100),
                        'name_font_size': int(obj.get('fontSize', 60)),
                        'name_color': obj.get('fill', '#000000'),
                    })
                    
                elif obj['id'] == 'date':
                    name_obj = next((o for o in layout['objects'] if o['id'] == 'name'), None)
                    if name_obj:
                        offset = obj['top'] - name_obj['top']
                        template.write({
                            'date_position_offset': int(offset),
                            'date_font_size': int(obj.get('fontSize', 30)),
                            'date_color': obj.get('fill', '#000000'),
                        })
                        
                elif obj['id'] == 'logo':
                    template.write({
                        'logo_position_x': int((obj['left'] / layout['canvas_width']) * 100),
                        'logo_position_y': int((obj['top'] / layout['canvas_height']) * 100),
                    })
                    
                elif obj['id'] == 'signature':
                    template.write({
                        'signature_position_x': int(((obj['left'] + obj['width']/2) / layout['canvas_width']) * 100),
                        'signature_position_y': int((obj['top'] / layout['canvas_height']) * 100),
                    })
            
            _logger.info("Layout saved successfully")
            return {'success': True}
            
        except Exception as e:
            _logger.error(f"Error saving layout: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/certificate/editor/load/<int:template_id>', type='json', auth='user')
    def load_editor_layout(self, template_id, **kwargs):
        """Load saved layout configuration"""
        template = request.env['survey.certificate.template'].browse(template_id)
        
        if not template.exists():
            return {'success': False, 'error': 'Template not found'}
        
        try:
            if template.layout_json:
                layout = json.loads(template.layout_json)
                _logger.info(f"Loaded layout for template {template.id}")
                return {
                    'success': True,
                    'layout': layout
                }
            else:
                _logger.info(f"No saved layout found for template {template.id}")
                return {'success': True, 'layout': None}
                
        except Exception as e:
            _logger.error(f"Error loading layout: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

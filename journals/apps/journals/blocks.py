""" Custom blocks """
import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup as parser
from django.utils import six
from wagtail.wagtailcore import blocks
from wagtail.wagtailcore.models import Page
from wagtail.wagtaildocs.blocks import DocumentChooserBlock
from wagtail.wagtailimages.blocks import ImageChooserBlock
from wagtail.wagtailcore.rich_text import extract_attrs, get_link_handler, get_embed_handler, FIND_A_TAG, FIND_EMBED_TAG

from journals.apps.journals.models import JournalDocument, Video
from journals.apps.journals.widgets import AdminVideoChooser
from journals.apps.journals.utils import get_image_url, get_span_id

PDF_BLOCK_TYPE = 'pdf'
VIDEO_BLOCK_TYPE = 'xblock_video'
IMAGE_BLOCK_TYPE = 'image'
RICH_TEXT_BLOCK_TYPE = 'rich_text'
RAW_HTML_BLOCK_TYPE = 'raw_html'
STREAM_DATA_TYPE_FIELD = 'type'
STREAM_DATA_DOC_FIELD = 'doc'
STREAM_DATA_VIDEO_FIELD = 'video'

log = logging.getLogger(__name__)


class VideoChooserBlock(blocks.ChooserBlock):
    """VideoChooserBlock component"""
    target_model = Video
    widget = AdminVideoChooser

    class Meta:
        icon = "media"

    # Return the key value for the select field
    def value_for_form(self, value):
        if isinstance(value, self.target_model):
            return value.pk
        else:
            return value


class PDFBlock(blocks.StructBlock):
    """PDFBlock component"""
    doc = DocumentChooserBlock()
    title = blocks.CharBlock(required=False, help_text='Override document title')

    def get_title(self, value):
        return value.get('title')

    def get_doc(self, value):
        return value.get(STREAM_DATA_DOC_FIELD)

    def get_searchable_content(self, value):
        return [self.get_title(value)]

    def get_api_representation(self, value, context=None):
        block_title = self.get_title(value)
        document = self.get_doc(value)

        if document:
            return {
                'doc_id': document.id,
                'title': block_title if block_title else document.title,
                'url': document.file.url,
                'span_id': get_span_id(PDF_BLOCK_TYPE, document.id),
            }

        log.warning('Missing Document: document has been deleted but still referenced in page')
        return {
            'doc_id': 0,
            'title': block_title if block_title else "Missing Document",
            'url': '',
            'span_id': 'missing-document',
        }


class JournalRichTextBlock(blocks.RichTextBlock):
    """JournalRichTextBlock component"""
    def get_searchable_content(self, value):
        return [parser(value.source, 'html.parser').get_text(' ')]

    @staticmethod
    def expand_db_html(html, for_editor=False, base_url='/'):
        """
        Override from wagtail.wagtailcore.rich_text to use full path
        to embedded images
        """
        def replace_a_tag(m):
            """
            overridden, return href for Pages and Documents that
            journals frontend knows how to display
            """
            attrs = extract_attrs(m.group(1))
            if 'linktype' not in attrs:
                # return unchanged
                return m.group(0)
            if attrs['linktype'] == 'page':
                try:
                    page = Page.objects.get(id=attrs['id'])
                    return '<a href="{page_path}">'.format(page_path=page.specific.get_frontend_page_path())
                except Page.DoesNotExist:
                    return "<a>"

            if attrs['linktype'] == 'document':
                try:
                    doc = JournalDocument.objects.get(id=attrs['id'])
                    return '<a href="{viewer_path}" target="_blank">'.format(viewer_path=doc.get_viewer_url(base_url))
                except Page.DoesNotExist:
                    return "<a>"

            handler = get_link_handler(attrs['linktype'])
            return handler.expand_db_attributes(attrs, for_editor)

        def replace_embed_tag(m):
            """
            overriden, change img src to be absolute url so it can be
            rendered by frontend
            """
            attrs = extract_attrs(m.group(1))
            handler = get_embed_handler(attrs['embedtype'])
            html = handler.expand_db_attributes(attrs, for_editor)
            if attrs['embedtype'] == 'image':
                html = html.replace('src="/', 'src="{}'.format(base_url))
            return html

        html = FIND_A_TAG.sub(replace_a_tag, html)
        html = FIND_EMBED_TAG.sub(replace_embed_tag, html)
        return html

    def get_api_representation(self, value, context=None):
        request = context['request']
        base_url = urljoin("{}://{}:{}".format(
            request.scheme,
            request.site.hostname,
            request.site.port,
        ), '/')
        return self.expand_db_html(value.source, base_url=base_url)


class JournalRawHTMLBlock(blocks.RawHTMLBlock):
    """JournalRawHTMLBlock component"""
    def value_for_form(self, value):
        """
        Strips dangerous tags from value
        """
        soup = parser(six.text_type(value), 'html.parser')
        forbidden_tags = soup.find_all(["script", "link", "frame", "iframe"])
        for tag in forbidden_tags:
            tag.extract()
        return str(soup)

    def get_searchable_content(self, value):
        return [parser(six.text_type(value), 'html.parser').get_text()]


class XBlockVideoBlock(blocks.StructBlock):
    """XBlockVideoBlock component"""
    video = VideoChooserBlock(required=True)
    title = blocks.CharBlock(required=False, help_text='Override video title')

    def get_title(self, value):
        return value.get('title')

    def get_video(self, value):
        return value.get(STREAM_DATA_VIDEO_FIELD)

    def get_searchable_content(self, value):
        return [self.get_title(value)]

    def get_api_representation(self, value, context=None):
        block_title = self.get_title(value)
        video = self.get_video(value)

        if video:
            return {
                'video_id': video.id,
                'title': block_title if block_title else video.display_name,
                'view_url': video.view_access_url,
                'transcript_url': video.transcript_url,
                'span_id': get_span_id(VIDEO_BLOCK_TYPE, video.id),
            }

        log.warning('Missing Video: video has been deleted but still referenced in page')
        return {
            'video_id': 0,
            'title': block_title if block_title else "Missing Video",
            'view_url': '',
            'transcript_url': '',
            'span_id': 'missing-video',
        }


class JournalImageChooserBlock(blocks.StructBlock):
    """ JournalImageChooserBlock component """
    image = ImageChooserBlock()
    title = blocks.CharBlock(required=False, help_text='Override image title')
    caption = blocks.RichTextBlock(
        required=False,
        help_text='Override image caption',
        features=['h1', 'h2', 'h3', 'ol', 'ul', 'bold', 'italic', 'link', 'hr', 'document-link']
    )

    def get_image(self, value):
        return value.get('image')

    def get_title(self, value):
        return value.get('title')

    def get_caption_text(self, value):
        block = self.get_caption_block(value)
        return block.source if block else block

    def get_caption_block(self, value):
        return value.get('caption')

    def get_searchable_content(self, value):
        block_caption = self.get_caption_block(value)
        if block_caption:
            searchable_caption = parser(six.text_type(self.get_caption_text(value)), 'html.parser').get_text()
        else:
            searchable_caption = None
        return [self.get_title(value), searchable_caption]

    def get_api_representation(self, value, context=None):
        block_title = self.get_title(value)
        block_caption = self.get_caption_block(value)
        image = self.get_image(value)

        if image:
            return {
                'title': block_title if block_title else image.title,
                'width': image.width,
                'height': image.height,
                'image_id': image.id,
                'url': get_image_url(context['request'].site, image),
                'caption': self.get_caption_text(value) if block_caption else image.caption,
                'span_id': get_span_id(IMAGE_BLOCK_TYPE, image.id)
            }

        log.warning('Missing Image: image has been deleted but still referenced in page')
        return {
            'title': block_title if block_title else "Missing Image",
            'width': 0,
            'height': 0,
            'image_id': 0,
            'url': '',
            'caption': self.get_caption_text(value) if block_caption else '',
            'span_id': 'missing-image',
        }

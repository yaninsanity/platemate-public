"""
Django admin configuration for SMS service.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import path, reverse
from django.shortcuts import render
from django import forms
from django.template import Template, Context
from datetime import timedelta

from .models import SMSRecord, OTPRecord, SMSTemplate
from .utils import mask_phone_number
from .services import get_sms_service, get_otp_service
from .exceptions import SMSSendError, OTPGenerationError


@admin.register(SMSRecord)
class SMSRecordAdmin(admin.ModelAdmin):
    """Admin interface for SMS records."""

    list_display = [
        'id',
        'masked_phone',
        'user_link',
        'status_badge',
        'is_read_badge',
        'attempts',
        'message_preview',
        'created_at',
        'sent_at'
    ]

    list_filter = [
        'status',
        'is_read',
        'created_at',
        'sent_at',
        ('user', admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        'phone_number',
        'formatted_phone',
        'message',
        'user__username',
        'user__email',
    ]

    readonly_fields = [
        'phone_number',
        'formatted_phone',
        'masked_phone_display',
        'user',
        'message',
        'status',
        'error_message',
        'textbelt_response_pretty',
        'attempts',
        'ip_address',
        'user_agent',
        'created_at',
        'sent_at',
    ]

    ordering = ['-created_at']

    date_hierarchy = 'created_at'

    def masked_phone(self, obj):
        """Display masked phone number."""
        return mask_phone_number(obj.formatted_phone or obj.phone_number)

    masked_phone.short_description = 'Phone Number'

    def masked_phone_display(self, obj):
        """Display both original and formatted phone numbers (masked)."""
        original = mask_phone_number(obj.phone_number)
        formatted = mask_phone_number(obj.formatted_phone) if obj.formatted_phone else 'N/A'
        return format_html(
            '<strong>Original:</strong> {}<br><strong>Formatted:</strong> {}',
            original, formatted
        )

    masked_phone_display.short_description = 'Phone Numbers'

    def user_link(self, obj):
        """Display user with link to user admin."""
        if obj.user:
            url = f"/admin/auth/user/{obj.user.pk}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'

    user_link.short_description = 'User'

    def is_read_badge(self, obj):
        """Display read status badge."""
        if obj.status != 'success':
            return '-'

        if obj.is_read:
            return format_html(
                '<span style="color: #6c757d;">Read</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ffc107; color: #212529; '
                'padding: 2px 8px; border-radius: 3px; font-weight: bold;">Unread</span>'
            )

    is_read_badge.short_description = 'Read Status'

    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'pending': '#FFA500',  # Orange
            'success': '#28a745',  # Green
            'failed': '#dc3545',  # Red
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )

    status_badge.short_description = 'Status'

    def message_preview(self, obj):
        """Display truncated message preview."""
        if len(obj.message) > 50:
            return f"{obj.message[:50]}..."
        return obj.message

    message_preview.short_description = 'Message'

    def textbelt_response_pretty(self, obj):
        """Display formatted JSON response."""
        if obj.textbelt_response:
            import json
            return format_html(
                '<pre style="background: #f5f5f5; padding: 10px; '
                'border-radius: 5px;">{}</pre>',
                json.dumps(obj.textbelt_response, indent=2)
            )
        return '-'

    textbelt_response_pretty.short_description = 'Textbelt Response'

    def has_add_permission(self, request):
        """Enable manual creation of SMS records."""
        return True

    def has_change_permission(self, request, obj=None):
        """Allow editing only for pending/failed messages."""
        if obj and obj.status in ['pending', 'failed']:
            return True
        return False

    actions = ['resend_failed_sms', 'send_test_sms', 'mark_as_read_action', 'mark_as_unread_action']

    readonly_fields = [
        'masked_phone_display',
        'textbelt_response_pretty',
        'formatted_phone',
        'status',
        'error_message',
        'attempts',
        'ip_address',
        'user_agent',
        'created_at',
        'sent_at',
    ]

    def get_fields(self, request, obj=None):
        """Define fields to display."""
        if obj:  # Viewing existing record
            return [
                'user',
                'phone_number',
                'formatted_phone',
                'message',
                'status',
                'error_message',
                'attempts',
                'textbelt_response_pretty',
                'ip_address',
                'user_agent',
                'created_at',
                'sent_at',
            ]
        else:  # Creating new record
            return ['phone_number', 'message', 'user']

    def get_readonly_fields(self, request, obj=None):
        """Dynamic readonly fields based on create/edit."""
        if obj:  # Editing existing record
            return [
                'phone_number',
                'formatted_phone',
                'user',
                'message',
                'status',
                'error_message',
                'textbelt_response_pretty',
                'attempts',
                'ip_address',
                'user_agent',
                'created_at',
                'sent_at',
            ]
        else:  # Creating new record
            return []

    def save_model(self, request, obj, form, change):
        """Override save to send SMS when creating new record."""
        if not change:  # New object
            # Don't save yet - let send_sms create the record
            try:
                sms_service = get_sms_service()
                record = sms_service.send_sms(
                    phone_number=obj.phone_number,
                    message=obj.message,
                    user=obj.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )
                # Update obj with the created record's id so Django redirects correctly
                obj.pk = record.pk
                messages.success(request, f"SMS sent successfully to {record.phone_number}")
            except Exception as e:
                # If sending fails, still save the record with failed status
                obj.status = 'failed'
                obj.error_message = str(e)
                obj.ip_address = request.META.get('REMOTE_ADDR')
                obj.user_agent = request.META.get('HTTP_USER_AGENT')
                super().save_model(request, obj, form, change)
                messages.error(request, f"Failed to send SMS: {str(e)}")
        else:
            super().save_model(request, obj, form, change)


    @admin.action(description='Send test SMS to selected numbers')
    def send_test_sms(self, request, queryset):
        """Send a test SMS to selected phone numbers."""
        phone_numbers = queryset.values_list('phone_number', flat=True).distinct()

        if 'send' in request.POST:
            message = request.POST.get('message')
            sms_service = get_sms_service()
            success_count = 0

            for phone in phone_numbers:
                try:
                    record = sms_service.send_sms(
                        phone_number=phone,
                        message=message,
                        user=request.user,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT')
                    )
                    success_count += 1
                except Exception as e:
                    messages.error(request, f"Failed to send to {phone}: {str(e)}")

            messages.success(request, f"Sent test SMS to {success_count} numbers.")
            return HttpResponseRedirect(request.get_full_path())

        # Inline template
        template_string = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Send Test SMS</title>
            <link rel="stylesheet" type="text/css" href="/static/admin/css/base.css">
            <link rel="stylesheet" type="text/css" href="/static/admin/css/forms.css">
        </head>
        <body class="change-form">
            <div id="container">
                <div id="header">
                    <div id="branding">
                        <h1 id="site-name">Django administration</h1>
                    </div>
                </div>
                <div id="content" class="colM">
                    <h1>Send Test SMS</h1>
                    <div id="content-main">
                        <form method="post">
                            {% csrf_token %}

                            <p>You are about to send a test SMS to the following phone numbers:</p>

                            <ul>
                                {% for phone in phone_numbers %}
                                    <li>{{ phone }}</li>
                                {% endfor %}
                            </ul>

                            <fieldset class="module aligned">
                                <div class="form-row">
                                    <label for="id_message" class="required">Message:</label>
                                    <textarea name="message" id="id_message" rows="4" cols="60" required>Test message from SMS Service</textarea>
                                    <p class="help">Enter the message to send to all selected phone numbers.</p>
                                </div>
                            </fieldset>

                            <div class="submit-row">
                                <input type="submit" name="send" value="Send SMS" class="default">
                                <input type="button" value="Cancel" onclick="window.history.back();">
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''

        template = Template(template_string)
        context = Context({
            'phone_numbers': phone_numbers,
            'csrf_token': request.META.get('CSRF_COOKIE', ''),
        })

        return HttpResponse(template.render(context))


@admin.register(OTPRecord)
class OTPRecordAdmin(admin.ModelAdmin):
    """Admin interface for OTP records."""

    list_display = [
        'id',
        'masked_phone',
        'user_link',
        'purpose',
        'status_badge',
        'attempts_display',
        'is_expired_display',
        'created_at',
        'expires_at',
    ]

    list_filter = [
        'status',
        'purpose',
        'created_at',
        'expires_at',
        ('user', admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        'phone_number',
        'formatted_phone',
        'otp_id',
        'user__username',
        'user__email',
        'purpose',
    ]

    readonly_fields = [
        'phone_number',
        'formatted_phone',
        'masked_phone_display',
        'user',
        'otp_id',
        'purpose',
        'status',
        'attempts',
        'generation_response_pretty',
        'verification_responses_pretty',
        'ip_address',
        'user_agent',
        'created_at',
        'expires_at',
        'verified_at',
        'last_attempt_at',
        'time_remaining',
    ]

    ordering = ['-created_at']

    date_hierarchy = 'created_at'

    def masked_phone(self, obj):
        """Display masked phone number."""
        return mask_phone_number(obj.formatted_phone or obj.phone_number)

    masked_phone.short_description = 'Phone Number'

    def masked_phone_display(self, obj):
        """Display both original and formatted phone numbers (masked)."""
        original = mask_phone_number(obj.phone_number)
        formatted = mask_phone_number(obj.formatted_phone) if obj.formatted_phone else 'N/A'
        return format_html(
            '<strong>Original:</strong> {}<br><strong>Formatted:</strong> {}',
            original, formatted
        )

    masked_phone_display.short_description = 'Phone Numbers'

    def user_link(self, obj):
        """Display user with link to user admin."""
        if obj.user:
            url = f"/admin/auth/user/{obj.user.pk}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'

    user_link.short_description = 'User'

    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'pending': '#FFA500',  # Orange
            'verified': '#28a745',  # Green
            'expired': '#6c757d',  # Gray
            'failed': '#dc3545',  # Red
            'max_attempts': '#dc3545',  # Red
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )

    status_badge.short_description = 'Status'

    def attempts_display(self, obj):
        """Display attempts with max attempts."""
        from django.conf import settings
        max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 3)
        color = '#dc3545' if obj.attempts >= max_attempts else '#212529'
        return format_html(
            '<span style="color: {};">{} / {}</span>',
            color, obj.attempts, max_attempts
        )

    attempts_display.short_description = 'Attempts'

    def is_expired_display(self, obj):
        """Display expiration status."""
        if obj.is_expired:
            return format_html(
                '<span style="color: #dc3545;">✗ Expired</span>'
            )
        else:
            return format_html(
                '<span style="color: #28a745;">✓ Valid</span>'
            )

    is_expired_display.short_description = 'Valid'

    def time_remaining(self, obj):
        """Display time remaining until expiration."""
        if obj.status in ['verified', 'expired', 'max_attempts', 'failed']:
            return '-'

        if not obj.expires_at:
            return '-'

        remaining = obj.expires_at - timezone.localtime(timezone.now())
        if remaining.total_seconds() <= 0:
            return format_html('<span style="color: #dc3545;">Expired</span>')

        minutes = int(remaining.total_seconds() / 60)
        seconds = int(remaining.total_seconds() % 60)

        color = '#dc3545' if minutes < 2 else '#FFA500' if minutes < 5 else '#28a745'
        return format_html(
            '<span style="color: {};">{} min {} sec</span>',
            color, minutes, seconds
        )

    time_remaining.short_description = 'Time Remaining'

    def generation_response_pretty(self, obj):
        """Display formatted generation response."""
        if obj.generation_response:
            import json
            return format_html(
                '<pre style="background: #f5f5f5; padding: 10px; '
                'border-radius: 5px;">{}</pre>',
                json.dumps(obj.generation_response, indent=2)
            )
        return '-'

    generation_response_pretty.short_description = 'Generation Response'

    def verification_responses_pretty(self, obj):
        """Display formatted verification responses."""
        if obj.verification_responses:
            import json
            return format_html(
                '<pre style="background: #f5f5f5; padding: 10px; '
                'border-radius: 5px; max-height: 300px; overflow-y: auto;">{}</pre>',
                json.dumps(obj.verification_responses, indent=2)
            )
        return '-'

    verification_responses_pretty.short_description = 'Verification Attempts'

    def has_add_permission(self, request):
        """Disable direct OTP creation - use Send OTP button instead."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make OTP records read-only."""
        return False

    actions = ['resend_otp', 'invalidate_otp']

    def changelist_view(self, request, extra_context=None):
        """Override changelist view to add Send OTP button."""
        extra_context = extra_context or {}

        # Add button info to context
        extra_context['send_otp_url'] = reverse('admin:sms_service_otprecord_send_otp')

        return super().changelist_view(request, extra_context)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Override changeform to show custom buttons."""
        extra_context = extra_context or {}

        # Since we disabled add permission, redirect add attempts to send OTP
        if object_id is None:
            return HttpResponseRedirect(reverse('admin:sms_service_otprecord_send_otp'))

        return super().changeform_view(request, object_id, form_url, extra_context)

    class Media:
        js = ('admin/js/otprecord_admin.js',)

    def verify_otp_link(self, obj):
        """Add verify link for pending OTPs."""
        if obj.status == 'pending' and not obj.is_expired:
            verify_url = reverse('admin:sms_service_otprecord_verify_otp', args=[obj.id])
            return format_html(
                '<a href="{}" class="button" style="background-color: #28a745; color: white; '
                'padding: 5px 10px; text-decoration: none; border-radius: 3px; '
                'display: inline-block;">Verify OTP</a>',
                verify_url
            )
        elif obj.status == 'verified':
            return format_html('<span style="color: #28a745;">✓ Verified</span>')
        elif obj.status == 'expired':
            return format_html('<span style="color: #dc3545;">Expired</span>')
        elif obj.status == 'max_attempts':
            return format_html('<span style="color: #dc3545;">Max Attempts</span>')
        return '-'

    verify_otp_link.short_description = 'Action'
    verify_otp_link.allow_tags = True

    def get_urls(self):
        """Add custom URLs for sending and verifying OTP."""
        urls = super().get_urls()
        custom_urls = [
            path('send-otp/', self.admin_site.admin_view(self.send_otp_view),
                 name='sms_service_otprecord_send_otp'),
            path('<int:otp_id>/verify/', self.admin_site.admin_view(self.verify_otp_view),
                 name='sms_service_otprecord_verify_otp'),
        ]
        return custom_urls + urls

    def verify_otp_view(self, request, otp_id):
        """Custom view for verifying OTP."""
        try:
            otp_record = OTPRecord.objects.get(id=otp_id)
        except OTPRecord.DoesNotExist:
            messages.error(request, "OTP record not found.")
            return HttpResponseRedirect(reverse('admin:sms_service_otprecord_changelist'))

        if request.method == 'POST':
            otp_code = request.POST.get('otp_code')
            otp_service = get_otp_service()

            try:
                success, message = otp_service.verify_otp(
                    phone_number=otp_record.phone_number,
                    otp_code=otp_code,
                    purpose=otp_record.purpose,
                    user=otp_record.user
                )

                if success:
                    messages.success(request, "OTP verified successfully!")
                else:
                    messages.warning(request, f"Verification failed: {message}")

            except Exception as e:
                messages.error(request, f"Error: {str(e)}")

            return HttpResponseRedirect(
                reverse('admin:sms_service_otprecord_change', args=[otp_id])
            )

        # Show verification form
        template_string = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Verify OTP - Django admin</title>
            <link rel="stylesheet" type="text/css" href="/static/admin/css/base.css">
            <link rel="stylesheet" type="text/css" href="/static/admin/css/forms.css">
        </head>
        <body class="change-form">
            <div id="container">
                <div id="header">
                    <div id="branding">
                        <h1 id="site-name">Django administration</h1>
                    </div>
                </div>

                <div id="content" class="colM">
                    <h1>Verify OTP</h1>

                    <div id="content-main">
                        <form method="post">
                            {% csrf_token %}

                            <fieldset class="module aligned">
                                <h2>OTP Details</h2>

                                <div class="form-row">
                                    <label>Phone Number:</label>
                                    <div class="readonly">{{ otp_record.formatted_phone }}</div>
                                </div>

                                <div class="form-row">
                                    <label>Purpose:</label>
                                    <div class="readonly">{{ otp_record.purpose }}</div>
                                </div>

                                <div class="form-row">
                                    <label>Status:</label>
                                    <div class="readonly">{{ otp_record.status }}</div>
                                </div>

                                <div class="form-row">
                                    <label>Attempts:</label>
                                    <div class="readonly">{{ otp_record.attempts }} / {{ max_attempts }}</div>
                                </div>

                                <div class="form-row">
                                    <label for="id_otp_code" class="required">Enter OTP Code:</label>
                                    <input type="text" name="otp_code" id="id_otp_code" 
                                           maxlength="6" required autofocus
                                           style="font-size: 20px; width: 200px; text-align: center;">
                                    <p class="help">Enter the 6-digit code sent to the phone</p>
                                </div>
                            </fieldset>

                            <div class="submit-row">
                                <input type="submit" value="Verify OTP" class="default">
                                <input type="button" value="Cancel" 
                                       onclick="window.location.href='{% url 'admin:sms_service_otprecord_change' otp_record.id %}';">
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''

        from django.template import Template, Context
        from django.template.context_processors import csrf
        from django.conf import settings

        template = Template(template_string)
        context_dict = {
            'otp_record': otp_record,
            'max_attempts': getattr(settings, 'OTP_MAX_ATTEMPTS', 3),
        }
        context_dict.update(csrf(request))
        context = Context(context_dict)

        return HttpResponse(template.render(context))

    def send_otp_view(self, request):
        """Custom view for sending OTP."""
        if request.method == 'POST':
            form = SendOTPForm(request.POST)
            if form.is_valid():
                try:
                    otp_service = get_otp_service()
                    record = otp_service.send_otp(
                        phone_number=form.cleaned_data['phone_number'],
                        purpose=form.cleaned_data['purpose'],
                        user=request.user if form.cleaned_data['purpose'] != 'test' else None,
                        message_template=form.cleaned_data.get('message_template'),
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT')
                    )

                    messages.success(
                        request,
                        f"OTP sent successfully to {mask_phone_number(record.formatted_phone)}. "
                        f"Record ID: {record.id}"
                    )

                    # Redirect to the OTP record detail page
                    return HttpResponseRedirect(
                        reverse('admin:sms_service_otprecord_change', args=[record.id])
                    )

                except Exception as e:
                    messages.error(request, f"Failed to send OTP: {str(e)}")
        else:
            form = SendOTPForm()

        # Inline template
        template_string = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Send OTP - Django admin</title>
            <link rel="stylesheet" type="text/css" href="/static/admin/css/base.css">
            <link rel="stylesheet" type="text/css" href="/static/admin/css/forms.css">
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                // Auto-format phone number as user types
                const phoneInput = document.querySelector('#id_phone_number');
                if (phoneInput) {
                    phoneInput.addEventListener('input', function(e) {
                        // Basic formatting for display
                        let value = e.target.value.replace(/\\D/g, '');
                        if (value.length >= 6) {
                            value = value.slice(0, 3) + '-' + value.slice(3, 6) + '-' + value.slice(6, 10);
                        } else if (value.length >= 3) {
                            value = value.slice(0, 3) + '-' + value.slice(3);
                        }
                        e.target.value = value;
                    });
                }
            });
            </script>
        </head>
        <body class="change-form">
            <div id="container">
                <div id="header">
                    <div id="branding">
                        <h1 id="site-name">Django administration</h1>
                    </div>
                    <div id="user-tools">
                        <a href="{% url 'admin:sms_service_otprecord_changelist' %}">← Back to OTP Records</a>
                    </div>
                </div>

                <div id="content" class="colM">
                    <h1>Send OTP Verification Code</h1>

                    <div id="content-main">
                        <form method="post" id="send-otp-form">
                            {% csrf_token %}

                            {% if messages %}
                                {% for message in messages %}
                                    <div class="messagelist">
                                        <div class="{{ message.tags }}">{{ message }}</div>
                                    </div>
                                {% endfor %}
                            {% endif %}

                            <fieldset class="module aligned">
                                <h2>OTP Details</h2>

                                {% for field in form %}
                                <div class="form-row">
                                    <label for="{{ field.id_for_label }}" {% if field.field.required %}class="required"{% endif %}>
                                        {{ field.label }}:
                                    </label>
                                    {{ field }}
                                    {% if field.help_text %}
                                        <p class="help">{{ field.help_text|safe }}</p>
                                    {% endif %}
                                    {% if field.errors %}
                                        <ul class="errorlist">
                                        {% for error in field.errors %}
                                            <li>{{ error }}</li>
                                        {% endfor %}
                                        </ul>
                                    {% endif %}
                                </div>
                                {% endfor %}
                            </fieldset>

                            <div class="submit-row">
                                <input type="submit" value="Send OTP" class="default">
                                <input type="button" value="Cancel" onclick="window.location.href='{% url 'admin:sms_service_otprecord_changelist' %}';">
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''

        from django.template import Template, Context
        from django.template.context_processors import csrf
        from django.contrib.messages import get_messages

        template = Template(template_string)
        context_dict = {
            'form': form,
            'messages': get_messages(request),
        }
        context_dict.update(csrf(request))
        context = Context(context_dict)

        return HttpResponse(template.render(context))

    @admin.action(description='Resend OTP for selected records')
    def resend_otp(self, request, queryset):
        """Resend OTP for failed or expired records."""
        otp_service = get_otp_service()
        success_count = 0

        for record in queryset:
            try:
                # Create new OTP for the same phone/purpose
                new_record = otp_service.send_otp(
                    phone_number=record.phone_number,
                    purpose=record.purpose,
                    user=record.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )
                success_count += 1

                # Mark old record as expired
                if record.status == 'pending':
                    record.status = 'expired'
                    record.save()

            except Exception as e:
                messages.error(request, f"Failed to resend OTP to {record.phone_number}: {str(e)}")

        if success_count:
            messages.success(request, f"Successfully resent {success_count} OTPs.")

    @admin.action(description='Invalidate selected OTPs')
    def invalidate_otp(self, request, queryset):
        """Mark selected OTPs as expired."""
        count = queryset.filter(status='pending').update(status='expired')
        messages.success(request, f"Invalidated {count} OTPs.")


# Create a form for manual OTP sending
class SendOTPForm(forms.Form):
    phone_number = forms.CharField(
        max_length=50,
        help_text="Enter phone number in any format (e.g., 555-123-4567)"
    )
    purpose = forms.ChoiceField(
        choices=[
            ('verification', 'Phone Verification'),
            ('login', 'Login'),
            ('password_reset', 'Password Reset'),
            ('test', 'Test'),
        ]
    )
    message_template = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Optional: Custom message template. Use $OTP for the code.",
        initial="Your verification code is $OTP"
    )


@admin.register(SMSTemplate)
class SMSTemplateAdmin(admin.ModelAdmin):
    """Admin interface for SMS templates."""

    list_display = [
        'name',
        'description_preview',
        'is_active',
        'created_at',
        'updated_at',
    ]

    list_filter = [
        'is_active',
        'created_at',
        'updated_at',
    ]

    search_fields = [
        'name',
        'description',
        'template',
    ]

    fields = [
        'name',
        'description',
        'template',
        'template_preview',
        'is_active',
        'created_at',
        'updated_at',
    ]

    readonly_fields = [
        'template_preview',
        'created_at',
        'updated_at',
    ]

    def description_preview(self, obj):
        """Display truncated description."""
        if obj.description and len(obj.description) > 60:
            return f"{obj.description[:60]}..."
        return obj.description or '-'

    description_preview.short_description = 'Description'

    def template_preview(self, obj):
        """Display template with highlighted variables."""
        import re
        template = obj.template
        # Highlight variables in template
        highlighted = re.sub(
            r'\{(\w+)\}',
            r'<span style="background-color: #fff3cd; padding: 2px 5px; '
            r'border-radius: 3px; font-weight: bold;">{\1}</span>',
            template
        )
        return format_html(
            '<div style="background: #f5f5f5; padding: 10px; '
            'border-radius: 5px; font-family: monospace;">{}</div>',
            highlighted
        )

    template_preview.short_description = 'Template Preview'


# Admin site customization
admin.site.site_header = 'SMS Service Administration'
admin.site.site_title = 'SMS Service'

# Bulk SMS sending page
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.template import RequestContext


User = get_user_model()


class BulkSMSAdmin(admin.ModelAdmin):
    """Special admin for bulk SMS sending."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        """Add custom URL for bulk SMS."""
        urls = super().get_urls()
        custom_urls = [
            path('', self.admin_site.admin_view(self.bulk_sms_view),
                 name='sms_service_bulksmsproxy_changelist'),
        ]
        return custom_urls + urls

    def bulk_sms_view(self, request):
        """Show bulk SMS sending interface."""
        if request.method == 'POST':
            # Handle bulk SMS sending
            user_ids = request.POST.getlist('users')
            message = request.POST.get('message', '').strip()

            if not user_ids:
                messages.error(request, "Please select at least one user.")
            elif not message:
                messages.error(request, "Please enter a message.")
            else:
                # Send SMS to selected users
                sms_service = get_sms_service()
                success_count = 0
                failed_count = 0

                users = User.objects.filter(id__in=user_ids)
                for user in users:
                    # Check if the user has a valid and verified phone number
                    phone = user.phone if user.phone else None

                    if phone:
                        try:
                            sms_service.send_sms(
                                phone_number=phone,
                                message=message,
                                user=user,
                                ip_address=request.META.get('REMOTE_ADDR'),
                                user_agent=request.META.get('HTTP_USER_AGENT')
                            )
                            success_count += 1
                        except Exception as e:
                            failed_count += 1
                            messages.warning(request, f"Failed to send to {user.username}: {str(e)}")
                    else:
                        failed_count += 1
                        messages.warning(request, f"User {user.username} does not have a verified phone number.")

                if success_count:
                    messages.success(request, f"Successfully sent SMS to {success_count} users.")
                if failed_count:
                    messages.error(request, f"Failed to send to {failed_count} users.")

        # Get users with phone numbers
        users = User.objects.all().order_by('username')

        # Filter users who might have phone numbers
        users_with_phones = []
        for user in User.objects.all().order_by('username'):
            if user.phone:  # 检查用户是否有电话号码
                users_with_phones.append({
                    'user': user,
                    'phone': mask_phone_number(user.phone),
                    'phone_verified': user.phone_verified,  # 使用 phone_verified 字段
                    'last_sms': SMSRecord.objects.filter(user=user).order_by('-created_at').first()
                })


        template_string = '''
            {% extends "admin/base_site.html" %}
            {% load i18n admin_urls static %}
            
            {% block extrastyle %}
            {{ block.super }}
            <style>
                #changelist { margin-top: 0; }
                .results { margin-top: 20px; }
                table { width: 100%; }
                td, th { padding: 8px; }
                .button { margin: 5px; }
                .messagelist { margin-bottom: 20px; }
                .help { font-size: 11px; color: #666; }
                #char-count { font-weight: bold; }
                .actions {
                    background: #f8f8f8;
                    padding: 10px;
                    margin-bottom: 10px;
                    border-radius: 4px;
                }
                .user-checkbox { cursor: pointer; }
                .submit-row {
                    padding: 10px 16px;
                    background: #f8f8f8;
                    border-top: 1px solid #ddd;
                    margin-top: 20px;
                }
            </style>
            {% endblock %}
            
            {% block breadcrumbs %}
            <div class="breadcrumbs">
                <a href="{% url 'admin:index' %}">{% trans 'Home' %}</a>
                &rsaquo; <a href="{% url 'admin:app_list' 'sms_service' %}">SMS Service</a>
                &rsaquo; Bulk SMS
            </div>
            {% endblock %}
            
            {% block content %}
            <h1>Send Bulk SMS</h1>
            
            <div id="content-main">
                {% if messages %}
                    <ul class="messagelist">
                        {% for message in messages %}
                            <li class="{{ message.tags }}">{{ message|safe }}</li>
                        {% endfor %}
                    </ul>
                {% endif %}
            
                <form method="post" id="bulk-sms-form">
                    {% csrf_token %}
            
                    <fieldset class="module aligned">
                        <h2>Message</h2>
                        <div class="form-row">
                            <label for="id_message" class="required">SMS Message:</label>
                            <textarea name="message" id="id_message" rows="4" cols="80" required
                                      placeholder="Enter the message to send to selected users..."
                                      style="width: 100%; max-width: 600px;"></textarea>
                            <p class="help">This message will be sent to all selected users below.</p>
                            <p class="help" id="char-count">0 characters</p>
                        </div>
                    </fieldset>
            
                    <div id="changelist">
                        <div class="actions">
                            <label>Select users to send SMS:</label>
                            <button type="button" onclick="selectAll(true)" class="button">Select All</button>
                            <button type="button" onclick="selectAll(false)" class="button">Deselect All</button>
                            <button type="button" onclick="selectVerified()" class="button">Select Verified Only</button>
                            <span id="selected-count" style="margin-left: 20px; font-weight: bold;">0 users selected</span>
                        </div>
            
                        <div class="results">
                            <table id="result_list">
                                <thead>
                                    <tr>
                                        <th style="width: 40px;">
                                            <input type="checkbox" id="select-all" onclick="selectAll(this.checked)">
                                        </th>
                                        <th>Username</th>
                                        <th>Email</th>
                                        <th>Phone</th>
                                        <th>Verified</th>
                                        <th>Last SMS</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in users_with_phones %}
                                    <tr class="row{% cycle '1' '2' %}">
                                        <td>
                                            <input type="checkbox" name="users" value="{{ item.user.id }}"
                                                   class="user-checkbox {% if item.phone_verified %}verified{% endif %}">
                                        </td>
                                        <td>{{ item.user.username }}</td>
                                        <td>{{ item.user.email|default:"-" }}</td>
                                        <td>{{ item.phone }}</td>
                                        <td>
                                            {% if item.phone_verified %}
                                                <img src="{% static 'admin/img/icon-yes.svg' %}" alt="True">
                                            {% else %}
                                                <img src="{% static 'admin/img/icon-no.svg' %}" alt="False">
                                            {% endif %}
                                        </td>
                                        <td>
                                            {% if item.last_sms %}
                                                {{ item.last_sms.created_at|date:"Y-m-d H:i" }}
                                                {% if item.last_sms.status == 'success' %}
                                                    <img src="{% static 'admin/img/icon-yes.svg' %}" alt="Success" width="16">
                                                {% else %}
                                                    <img src="{% static 'admin/img/icon-no.svg' %}" alt="Failed" width="16">
                                                {% endif %}
                                            {% else %}
                                                <span style="color: #999;">Never</span>
                                            {% endif %}
                                        </td>
                                    </tr>
                                    {% empty %}
                                    <tr>
                                        <td colspan="6" style="text-align: center; padding: 20px;">
                                            No users with phone numbers found.
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
            
                        <p class="paginator">
                            {{ total_users }} users with phone numbers
                        </p>
                    </div>
            
                    <div class="submit-row">
                        <input type="submit" value="Send SMS" class="default"
                               onclick="return confirm('Send SMS to ' + getSelectedCount() + ' selected users?');">
                    </div>
                </form>
            </div>
            
            <script>
            function selectAll(checked) {
                document.querySelectorAll('.user-checkbox').forEach(function(cb) {
                    cb.checked = checked;
                });
                updateSelectedCount();
            }
            
            function selectVerified() {
                document.querySelectorAll('.user-checkbox').forEach(function(cb) {
                    cb.checked = cb.classList.contains('verified');
                });
                updateSelectedCount();
            }
            
            function getSelectedCount() {
                return document.querySelectorAll('.user-checkbox:checked').length;
            }
            
            function updateSelectedCount() {
                var count = getSelectedCount();
                document.getElementById('selected-count').textContent = count + ' users selected';
            }
            
            // Update character count
            document.getElementById('id_message').addEventListener('input', function() {
                var count = this.value.length;
                document.getElementById('char-count').textContent = count + ' characters';
                if (count > 160) {
                    document.getElementById('char-count').style.color = '#dc3545';
                    document.getElementById('char-count').textContent += ' (will be sent as multiple SMS)';
                } else {
                    document.getElementById('char-count').style.color = '#495057';
                }
            });
            
            // Update count on checkbox change
            document.querySelectorAll('.user-checkbox').forEach(function(cb) {
                cb.addEventListener('change', updateSelectedCount);
            });
            
            // Initial count
            updateSelectedCount();
            </script>
            {% endblock %}
        '''

        template = Template(template_string)

        # Prepare context
        context = Context({
            'title': 'Send Bulk SMS',
            'users_with_phones': users_with_phones,
            'total_users': len(users_with_phones),
            'opts': self.model._meta,
            'has_view_permission': True,
            'site_title': admin.site.site_title,
            'site_header': admin.site.site_header,
            'app_label': 'sms_service',
        })

        # Use Django's render instead of inline template
        # return render(request, 'admin/sms_service/bulk_sms.html', context)

        # return HttpResponse(template.render(context))
        return HttpResponse(template.render(RequestContext(request, context)))


# Register a proxy model for bulk SMS
class BulkSMSProxy(SMSRecord):
    class Meta:
        proxy = True
        verbose_name = 'Bulk SMS'
        verbose_name_plural = 'Bulk SMS'


# Register the bulk SMS admin
admin.site.register(BulkSMSProxy, BulkSMSAdmin)




def generate_mail_content(candidate_name: str, position: str, is_eligible: bool, id: str, password: str) -> dict[str, str]:

    print(f"Generating email content for {candidate_name}, position: {position}, eligible: {is_eligible}")
    
    organisation = "Acme Corp"
    sender_name = "Jane Doe"
    sender_title = "HR Manager"
    company_name = "Acme Corp"
    link = f"http://agent.hostmyidea.me/?id={id}"

    """Generate HTML content for the email."""
    if is_eligible:
        subject = f"Interview Shortlist — {position} at {organisation}"
        html_content = f"""
          <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width,initial-scale=1" />
          <title>Interview Shortlist — {position} at {organisation}</title>
        </head>
        <body style="margin:0;padding:0;background-color:#f4f6f8;font-family:Arial, Helvetica, sans-serif;color:#1f2937;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f8;padding:28px 16px;">
            <tr>
              <td align="center">
          <table role="presentation" width="620" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(16,24,40,0.05);">
            <tr>
              <td style="padding:24px;">
                <!-- Header -->
                <div style="margin-bottom:18px;">
            <h2 style="margin:0;font-size:20px;color:#0b1220;">Application Update</h2>
                </div>

                <!-- Greeting -->
                <p style="margin:0 0 16px 0;font-size:15px;line-height:1.6;color:#111827;">
            Dear <strong>{candidate_name}</strong>,
                </p>

                <!-- Body -->
                <p style="margin:0 0 12px 0;font-size:15px;line-height:1.6;">
            Congratulations! Your application has been <strong>shortlisted</strong> for further consideration for the position of <strong>{position}</strong> at <strong>{organisation}</strong>. This is indeed a testament to your impressive qualifications and professional experience.
                </p>

                <p style="margin:0 0 12px 0;font-size:15px;line-height:1.6;">
            The next step in our process is to arrange a more in-depth discussion with you. This will provide us with an opportunity to better understand your skills and experiences, and will also give you a chance to learn more about the role, our team, and the organization in general.
                </p>

                <p style="margin:0 0 20px 0;font-size:15px;line-height:1.6;">
            We will get in touch with you shortly to schedule this discussion. If you have any preferred times or constraints, feel free to reply to this email and let us know.
                </p>

                <!-- Interview link button -->
                <p style="margin:0 0 8px 0;">
            <a href="{link}" style="display:inline-block;background-color:#2563eb;color:#ffffff;padding:10px 16px;border-radius:6px;text-decoration:none;font-weight:600;">View interview details & schedule</a>
                </p>

                <p style="margin:0 0 12px 0;font-size:13px;color:#6b7280;">
            If the button doesn't work, copy and paste this link into your browser:<br/>
            <a href="{link}" style="color:#2563eb;text-decoration:none;">{link}</a>
                </p>
                <!-- Credentials -->
                <p style="margin:0 0 20px 0;font-size:15px;line-height:1.6;">
            For your reference, here are your login credentials:<br/>
            Password: <strong>{password}</strong>
                </p>

                <!-- Signature -->
                <p style="margin:0;font-size:15px;line-height:1.6;color:#111827;">
            Best regards,<br/>
            <strong>{sender_name}</strong><br/>
            <span style="color:#6b7280;font-size:14px;">{sender_title} — {organisation}</span>
                </p>
              </td>
            </tr>

            <!-- Footer -->
            <tr>
              <td style="background-color:#f8fafc;padding:12px 24px;text-align:center;color:#6b7280;font-size:13px;">
                Questions? Reply to this email or contact us at <a href="mailto:hr@{organisation.lower()}.com" style="color:#2563eb;text-decoration:none;">hr@{organisation.lower()}.com</a>.
              </td>
            </tr>
          </table>
              </td>
            </tr>
          </table>
        </body>
        </html>

          """
    else:
        subject = f"Application Update — {position} at {organisation}"
        html_content = f"""
        <!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Application Update</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f7fa;font-family:Arial, Helvetica, sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f7fa;padding:24px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.08);overflow:hidden;">
          <tr>
            <td style="padding:24px;">
              <!-- Header -->
              <div style="text-align:left;margin-bottom:18px;">
                <h2 style="margin:0;color:#111827;font-size:20px;">Application Update</h2>
              </div>

              <!-- Body -->
              <p style="margin:0 0 16px 0;color:#333;font-size:15px;line-height:1.6;">
                Hi <strong>{candidate_name}</strong>,
              </p>

              <p style="margin:0 0 16px 0;color:#333;font-size:15px;line-height:1.6;">
                Thank you for your application. We appreciate you taking the time to submit your resume in the interest of learning about the <strong>{position}</strong> opportunity here at <strong>{organisation}</strong>.
              </p>

              <p style="margin:0 0 16px 0;color:#333;font-size:15px;line-height:1.6;">
                After careful consideration, we will not be moving forward with your application at this time as we have decided to move forward with other candidates whose skills and experience are a closer match to our requirements for this specific role.
              </p>

              <p style="margin:0 0 24px 0;color:#333;font-size:15px;line-height:1.6;">
                Best of luck in your career search.
              </p>

              <!-- Signature -->
              <p style="margin:0;color:#333;font-size:15px;line-height:1.6;">
                Sincerely,<br/>
                <strong>{sender_name}</strong><br/>
                <span style="color:#6b7280;font-size:14px;">{sender_title} — {organisation}</span>
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color:#f7fafc;padding:12px 24px;text-align:center;color:#6b7280;font-size:13px;">
              If you have any questions, reply to this email or contact us at <a href="mailto:hr@{organisation.lower()}.com" style="color:#2563eb;text-decoration:none;">hr@{organisation.lower()}.com</a>.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>

        """

    return {
        "subject": subject,
        "html_content": html_content
    }


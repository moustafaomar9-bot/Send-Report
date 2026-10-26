import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

st.set_page_config(
    page_title="Sales Report Auto Sender",
    page_icon="📊",
    layout="wide"
)

# Email credentials
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "momar@onlinemediaintl.com"
SENDER_PASSWORD = "bafy dktb dbml uwhh"

st.title("📊 Sales Daily Performance Report Sender (HTML Attachment)")
st.markdown("---")

# Smart matching function for Agent Name / Code with filename
def is_report_match(agent_name, agent_code, filename):
    filename_clean = str(filename).lower().replace("_", " ").replace("-", " ")

    # 1. Match by Agent Code if present
    if pd.notna(agent_code) and str(int(agent_code)) in filename_clean:
        return True

    # 2. Match by First two names of the agent
    name_parts = str(agent_name).strip().lower().split()
    if len(name_parts) >= 2:
        if name_parts[0] in filename_clean and name_parts[1][:3] in filename_clean:
            return True
    elif len(name_parts) == 1:
        if name_parts[0] in filename_clean:
            return True

    return False

# 1. File Uploaders
col1, col2 = st.columns(2)

with col1:
    excel_file = st.file_uploader("📂 1. Upload Excel Sheet", type=["xlsx", "xls", "csv"])

with col2:
    html_files = st.file_uploader("🌐 2. Upload HTML Reports", type=["html"], accept_multiple_files=True)

if excel_file and html_files:
    try:
        df = pd.read_excel(excel_file) if excel_file.name.endswith(('.xlsx', '.xls')) else pd.read_csv(excel_file)

        # Clean column headers
        df.columns = [col.strip() for col in df.columns]

        name_col = 'Agent Name' if 'Agent Name' in df.columns else df.columns[0]
        email_col = 'Email' if 'Email' in df.columns else df.columns[1]
        code_col = 'Agent Code' if 'Agent Code' in df.columns else None

        reports_dict = {file.name: file.getvalue() for file in html_files}

        st.success(f"✅ Excel loaded successfully ({len(df)} sales agents) | {len(reports_dict)} HTML reports uploaded")
        st.markdown("---")

        # 2. Select Recipients & Preview
        st.subheader("🎯 3. Select Recipients & Live Preview")

        agent_options = df[name_col].tolist()
        selected_agents = st.multiselect("👤 Select specific agents (Leave empty to send to all):", agent_options)

        if selected_agents:
            target_df = df[df[name_col].isin(selected_agents)]
        else:
            target_df = df

        st.info(f"📋 Target agents to receive report: {len(target_df)}")

        # 3. Report Preview
        st.subheader("👁️ Preview Agent Report")
        preview_agent = st.selectbox("Select agent to preview HTML report:", agent_options)

        if preview_agent:
            agent_row = df[df[name_col] == preview_agent].iloc[0]
            a_code = agent_row[code_col] if code_col else ""

            matched_bytes = None
            matched_filename = ""
            for fname, fbytes in reports_dict.items():
                if is_report_match(preview_agent, a_code, fname):
                    matched_bytes = fbytes
                    matched_filename = fname
                    break

            if matched_bytes:
                st.caption(f"📁 Matched File: `{matched_filename}`")
                st.components.v1.html(matched_bytes.decode("utf-8", errors="ignore"), height=500, scrolling=True)
            else:
                st.warning(f"⚠️ No matching HTML file found for `{preview_agent}`.")

        st.markdown("---")

        # 4. Dispatch Button
        st.subheader("🚀 4. Start Email Dispatch")

        if st.button("📧 Send Reports Now (as Attachments)", type="primary"):
            progress_bar = st.progress(0)
            success_count = 0
            fail_count = 0

            try:
                server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
                server.login(SENDER_EMAIL, SENDER_PASSWORD)

                for idx, (_, row) in enumerate(target_df.iterrows()):
                    agent_name = str(row[name_col]).strip()
                    agent_email = str(row[email_col]).strip()
                    agent_code = row[code_col] if code_col else ""

                    # Find matching file
                    html_bytes = None
                    attachment_filename = ""
                    for fname, fbytes in reports_dict.items():
                        if is_report_match(agent_name, agent_code, fname):
                            html_bytes = fbytes
                            attachment_filename = fname
                            break

                    if html_bytes and pd.notna(agent_email) and "@" in agent_email:
                        msg = MIMEMultipart()
                        msg["Subject"] = f"📊 Daily Performance Report - {agent_name}"
                        msg["From"] = f"Xclusives IT <{SENDER_EMAIL}>"
                        msg["To"] = agent_email

                        # 1. English Email Body
                        body_text = f"""Dear {agent_name},

Hope this email finds you well.

Please find attached your Daily Performance Report (HTML format). 
Kindly download and open the attached file in your browser to review your complete performance metrics.

Best regards,
Data Management & IT Team
Xclusives IT
"""
                        msg.attach(MIMEText(body_text, "plain", "utf-8"))

                        # 2. Attach HTML File
                        att = MIMEApplication(html_bytes, _subtype="html")
                        att.add_header('Content-Disposition', 'attachment', filename=attachment_filename)
                        msg.attach(att)

                        server.sendmail(SENDER_EMAIL, agent_email, msg.as_string())
                        success_count += 1
                        st.write(f"✅ Sent successfully to: **{agent_name}** ({agent_email}) | File: `{attachment_filename}`")
                    else:
                        fail_count += 1
                        st.write(f"❌ Failed to send to: **{agent_name}** (Reason: Matching HTML report not found)")

                    progress_bar.progress((idx + 1) / len(target_df))

                server.quit()
                st.balloons()
                st.success(f"🎉 Process completed! Sent {success_count} reports successfully, skipped {fail_count}.")

            except Exception as e:
                st.error(f"Error connecting to mail server: {e}")

    except Exception as e:
        st.error(f"Error reading dataset file: {e}")

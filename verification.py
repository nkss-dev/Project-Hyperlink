import discord, sqlite3, json, smtplib, os, math, random
from discord.ext import commands
from discord.utils import get
from email.message import EmailMessage
from dotenv import load_dotenv
load_dotenv()

sections = ['CE-A', 'CE-B', 'CE-C', 'CS-A', 'CS-B', 'EC-A', 'EC-B', 'EC-C', 'EE-A', 'EE-B', 'EE-C', 'IT-A', 'IT-B', 'ME-A', 'ME-B', 'ME-C', 'PI-A', 'PI-B']
subsections = ['CE-01', 'CE-02', 'CE-03', 'CE-04', 'CE-05', 'CE-06', 'CE-07', 'CE-08', 'CE-09',
            'CS-01', 'CS-02', 'CS-03', 'CS-04', 'CS-05', 'CS-06',
            'EC-01', 'EC-02', 'EC-03', 'EC-04', 'EC-05', 'EC-06', 'EC-07', 'EC-08', 'EC-09',
            'EE-01', 'EE-02', 'EE-03', 'EE-04', 'EE-05', 'EE-06', 'EE-07', 'EE-08', 'EE-09',
            'IT-01', 'IT-02', 'IT-03', 'IT-04', 'IT-05', 'IT-06',
            'ME-01', 'ME-02', 'ME-03', 'ME-04', 'ME-05', 'ME-06', 'ME-07', 'ME-08', 'ME-09',
            'PI-01', 'PI-02', 'PI-03', 'PI-04', 'PI-05', 'PI-06'
        ]

class Verify(commands.Cog):
    def __init__(self):
        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()
        try:
            with open('db/codes.json') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {}
        self.string1 = '''<!DOCTYPE html>
        <html>
        <body class="body" style="padding:0 !important; margin:0 auto !important; display:block !important; min-width:100% !important; width:100% !important; background:#ffffff; -webkit-text-size-adjust:none;">
        <center>
            <table width="100%" border="0" cellspacing="0" cellpadding="0"style="margin: 0; padding: 0; width: 100%; height: 100%;" bgcolor="#ffffff" class="gwfw">
                <tr>
                    <td style="margin: 0; padding: 0; width: 100%; height: 100%;" align="center" valign="top">
                        <table width="775" border="0" cellspacing="0" cellpadding="0"class="m-shell">
                            <tr>
                                <td class="td" style="width:775px; min-width:775px; font-size:0pt; line-height:0pt; padding:0; margin:0; font-weight:normal;">
                                    <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                        <!-- Main -->
                                        <tr>
                                            <td class="p-80 mpy-35 mpx-15" bgcolor="#212429" style="padding: 80px;">
                                                <table width="100%" border="0" cellspacing="0" cellpadding="0">


        			<table width="100%" border="0" cellspacing="0" cellpadding="0">
        				<tr>
        					<td class="title-36 pb-30 c-grey6 fw-b" style="font-size:36px; line-height:42px; font-family:'Motiva Sans', Helvetica, Arial, sans-serif; text-align:left; padding-bottom: 30px; color:#bfbfbf; font-weight:bold;">Dear '''
        self.string2 = ''',</td>
        				</tr>
        			</table>
        						<table width="100%" border="0" cellspacing="0" cellpadding="0">
        				<tr>
        					<td class="text-18 c-grey4 pb-30" style="font-size:18px; line-height:25px; font-family:'Motiva Sans', Helvetica, Arial, sans-serif; text-align:left; color:#dbdbdb; padding-bottom: 30px;">Here is the one-time password that you need to enter:</td>
        				</tr>
        			</table>
        						<table width="100%" border="0" cellspacing="0" cellpadding="0">
        				<tr>
        					<td class="pb-70 mpb-50" style="padding-bottom: 70px;">
        						<table width="100%" border="0" cellspacing="0" cellpadding="0"bgcolor="#17191c">
        							<tr>
        								<td class="py-30 px-56" style="padding-top: 30px; padding-bottom: 30px; padding-left: 56px; padding-right: 56px;">
        									<table width="100%" border="0" cellspacing="0" cellpadding="0">
        										<tr>
        											<td class="title-48 c-blue1 fw-b a-center" style="font-size:48px; line-height:52px; font-family:'Motiva Sans', Helvetica, Arial, sans-serif; color:#3a9aed; font-weight:bold; text-align:center;">
        												'''
        self.string3 = '''											</td>
        										</tr>
        									</table>
        								</td>
        							</tr>
        						</table>
        					</td>
        				</tr>
        			</table>
        						<table width="100%" border="0" cellspacing="0" cellpadding="0">
        				<tr>
        					<td class="text-18 c-grey4 pb-30" style="font-size:18px; line-height:25px; font-family:'Motiva Sans', Helvetica, Arial, sans-serif; text-align:left; color:#dbdbdb; padding-bottom: 30px;">This email was generated because of a verification attempt on the '''
        self.string4 = ''' Discord server.<br><br>
        To complete the verification, go to this <a style="color: #c6d4df;" href="https://discord.com/channels/783215699707166760/824549068344131645">channel</a> on the server and type:  <span style="color: #ffffff; font-weight: bold;">%verify code '''
        self.string5 = '''</span><br><br>
        <span style="color: #ffffff; font-weight: bold;">If you are not attempting to login</span> then please contact me (Contact details given at the end of this email) so that nobody chats on the server under your name.</td>
        				</tr>
        			</table>
        			            <table width="100%" border="0" cellspacing="0" cellpadding="0">
                        <tr>
                            <td class="text-18 c-blue1 pb-40" style="font-size:18px; line-height:25px; font-family:'Motiva Sans', Helvetica, Arial, sans-serif; text-align:left; color:#3a9aed; padding-bottom: 0px;"></td>
                        </tr>
                    </table>
                                                                    <!-- Signature -->
                                                        <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                                            <tr>
                                                                <td class="pt-30" style="padding-top: 20px;">
                                                                    <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                                                        <tr>
                                                                            <td class="img" width="3" bgcolor="#3a9aed" style="font-size:0pt; line-height:0pt; text-align:left;"></td>
                                                                            <td class="img" width="37" style="font-size:0pt; line-height:0pt; text-align:left;"></td>
                                                                            <td>
                                                                                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                                                                    <tr>
                                                                                                                                                                            <td class="text-16 py-20 c-grey4 fallback-font" style="font-size:16px; line-height:22px; font-family:'Motiva Sans', Helvetica, Arial, sans-serif; text-align:left; padding-top: 20px; padding-bottom: 20px; color:#f1f1f1;">
                                                                                                Cheers,<br />
        Priyanshu Tripathi                                                                                    </td>
                                                                                                                                                                    </tr>
                                                                                </table>
                                                                            </td>
                                                                        </tr>
                                                                    </table>
                                                                </td>
                                                            </tr>
                                                        </table>
                                                        <!-- END Signature -->

                                                        </td>
                                                    </tr>

                                                </table>
                                            </td>
                                        </tr>
                                        <!-- END Main -->

                                        <!-- Footer -->
                                        <tr>
                                            <td class="py-60 px-90 mpy-40 mpx-15" style="padding-top: 60px; padding-bottom: 0px; padding-left: 90px; padding-right: 90px;">
                                                <table width="100%" border="0" cellspacing="0" cellpadding="0">

                                                    <tr>
                                                        <td class="text-18 pb-60 mpb-40 fallback-font" style="font-size:18px; line-height:25px; color:#000001; font-family:'Motiva Sans', Helvetica, Arial, sans-serif; text-align:left; padding-bottom: 60px;">
        			                                        This email message was auto-generated. If you want to reach out to me, respond to this email or to any of my social media handles given below                                                    <br /><br />
                                                        </td>
                                                    </tr>

                                                    <!-- B -->
                                                                                                    <tr>
                                                            <td class="pb-80" style="padding-bottom: 80px;">
                                                                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                                                    <tr>
                                                                        <th class="column" width="100" style="font-size:0pt; line-height:0pt; padding:0; margin:0; font-weight:normal;">
                                                                            <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                                                                <tr>
                                                                                    <td class="img mpt-0" style="font-size:0pt; line-height:0pt; text-align:left;">
                                                                                        <img src="https://cdn.iconscout.com/icon/free/png-256/discord-2752210-2285027.png" width="32" height="32" border="0" alt="" />
                                                                                    </td>
                                                                                    <td class="text-18 pb-60 mpb-40 fallback-font" style="font-size:18px; line-height:2px; color:#000001; font-family:'Motiva Sans', Helvetica, Arial, sans-serif; text-align:left; padding-bottom: 0px;">
                                    			                                        GetPsyched#6675                                                    <br /><br />
                                                                                    </td>
                                                                                    <td class="img mpt-0" style="font-size:0pt; line-height:0pt; text-align:left;">
                                                                                        <img src="https://cdn.exclaimer.com/Handbook%20Images/instagram-icon_32x32.png" width="32" height="32" border="0" alt="" />
                                                                                    </td>
                                                                                    <td class="text-18 pb-60 mpb-40 fallback-font" style="font-size:18px; line-height:2px; color:#000001; font-family:'Motiva Sans', Helvetica, Arial, sans-serif; text-align:left; padding-bottom: 0px;">
                                    			                                        priy.ansh_                                                    <br /><br />
                                                                                    </td>
                                                                                    <td class="img mpt-0" style="font-size:0pt; line-height:0pt; text-align:left;">
                                                                                        <img src="https://cdn.exclaimer.com/Handbook%20Images/whatsapp_32.png" width="32" height="32" border="0" alt="" />
                                                                                    </td>
                                                                                    <td class="text-18 pb-60 mpb-40 fallback-font" style="font-size:18px; line-height:2px; color:#000001; font-family:'Motiva Sans', Helvetica, Arial, sans-serif; text-align:left; padding-bottom: 0px;">
                                    			                                        +971507805446                                                    <br /><br />
                                                                                    </td>
                                                                                </tr>
                                                                            </table>
                                                                        </th>
                                                                    </tr>
                                                                </table>
                                                            </td>
                                                        </tr>

                                                </table>
                                            </td>
                                        </tr>
                                    <!-- END Footer -->
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </center>


        </body>
        </html>
        '''

    def generateotp(self):
        sample_set = '01234567890123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        OTP = ''
        for i in range(5):
            OTP += sample_set[math.floor(random.random() * 46)]
        return OTP

    async def verify_basic(self, ctx, args):
        section = args[0]
        roll_no = int(args[1])
        self.c = self.conn.cursor()
        # Gets the record of the given roll number
        self.c.execute('SELECT * from main where Roll_Number = (:roll)', {'roll': roll_no})
        tuple = self.c.fetchone()
        # Exit if roll number doesn't exist
        if not tuple:
            await ctx.send(f'The requested record was not found, {ctx.author.mention}. Please re-check the entered details and try again')
            return
        # Exit if entered section doesn't match an existing section
        if section not in sections:
            await ctx.send(f'"{section}" is not an existing section, {ctx.author.mention}.\nPlease re-check the entered details and try again')
            return
        # Exit if entered section doesn't match the section that the roll number is bound to
        if section != tuple[2]:
            await ctx.send(f'The section that you entered does not match that of the roll number that you entered, {ctx.author.mention}.\nPlease re-check the entered details and try again')
            return
        # Exit if the record is already claimed by another user
        if tuple[9]:
            await ctx.send(f'The details you entered is of a record already claimed by `{tuple[9]}` {ctx.author.mention}.\nTry another record. If you think this was a mistake, contact a moderator.')
            return
        # Assigning one SubSection and one Section role to the user
        role = discord.utils.get(ctx.guild.roles, name = tuple[2])
        await ctx.author.add_roles(role)
        role = discord.utils.get(ctx.guild.roles, name = tuple[3])
        await ctx.author.add_roles(role)
        await ctx.send(f'Your record was found and verified {ctx.author.mention}!\nYou will now be removed from this channel.')
        # Removing the 'Not-Verified' role from the user
        role = discord.utils.get(ctx.guild.roles, name = 'Not-Verified')
        await ctx.author.remove_roles(role)
        # Updating the record in the database
        self.c.execute('UPDATE main SET Discord_UID = (:uid) WHERE Roll_Number = (:roll)', {'uid': ctx.author.id, 'roll': roll_no})
        self.conn.commit()
        # Changing the nick of the user to their first name
        word = tuple[4].split(' ')[0]
        await ctx.author.edit(nick = word[:1] + word[1:].lower())

    async def verify_email(self, ctx, args):
        EMAIL = os.getenv('EMAIL')
        msg = EmailMessage()
        msg['Subject'] = f'Verification of {ctx.author} on {ctx.guild}'
        msg['From'] = EMAIL
        msg['To'] = args[0]
        name_capital = args[1].split(' ')
        name = ''
        for word in name_capital:
            name += word[:1] + word[1:].lower() + ' '
        otp = self.generateotp()
        self.data[str(ctx.author.id)] = otp
        self.save()
        msg.set_content(f'{self.string1}{name.strip()}{self.string2}{otp}{self.string3}{ctx.guild}{self.string4}{otp}{self.string5}', subtype='html')

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL, os.getenv('PASSWORD'))
            smtp.send_message(msg)
        await ctx.send(f'Email sent successfully, {ctx.author.mention}!')

    @commands.command(name='verify')
    async def verify(self, ctx, *args):
        self.c.execute('SELECT Name, Institute_Email, Verified from main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        # Exit if the author is already in the database
        details = self.c.fetchone()
        if details and 'True' in details[2]:
            await ctx.send('You\'re already verified!')
            return
        if not details:
            await self.verify_basic(ctx, args)
        elif 'False' in details[2]:
            if ctx.channel.slowmode_delay < 5:
                await ctx.send(f'You can only use this command in a channel which has slowmode enabled, {ctx.author.mention}.')
                return
            if 'code' in args[0].lower():
                if str(ctx.author.id) in self.data:
                    if self.data[str(ctx.author.id)] == args[1]:
                        await ctx.send(f'Your email has been verified successfully, {ctx.author.mention}!')
                        del self.data[str(ctx.author.id)]
                        self.c.execute('UPDATE main SET Verified = "True" where Discord_UID = (:uid)', {'uid': ctx.author.id})
                        self.conn.commit()
                    else:
                        await ctx.send(f'The code you entered is incorrect, {ctx.author.mention}.')
                return
            if details[1].lower() == args[0].lower():
                await self.verify_email(ctx, [details[1], details[0]])
            else:
                await ctx.send(f'The email that you entered does not match your institute email, {ctx.author.mention}. Please try again with a valid email.\nIf you think this was a mistake, contact a mod.')

    def save(self):
        with open('db/codes.json', 'w') as f:
            json.dump(self.data, f)

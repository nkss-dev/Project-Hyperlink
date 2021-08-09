import discord, sqlite3, json, smtplib, os, math, random
from discord.ext import commands
from discord.utils import get
from email.message import EmailMessage
from dotenv import load_dotenv
load_dotenv()

def basicVerificationCheck(ctx):
    return ctx.bot.basicVerificationCheck(ctx)

class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

        try:
            with open('db/codes.json') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {}
        with open('db/emojis.json') as f:
            self.emojis = json.load(f)['utility']

        self.sections = (
            'CE-A', 'CE-B', 'CE-C',
            'CS-A', 'CS-B',
            'EC-A', 'EC-B', 'EC-C',
            'EE-A', 'EE-B', 'EE-C',
            'IT-A', 'IT-B',
            'ME-A', 'ME-B', 'ME-C',
            'PI-A', 'PI-B'
        )

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

    @commands.group(brief='Registers the user in the database')
    async def verify(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply('Invalid verification command passed.')
            return

        self.c.execute('SELECT Verified from main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        details = self.c.fetchone()
        if details:
            if details[0] == 'False':
                if ctx.invoked_subcommand.name == 'basic':
                    raise commands.CheckFailure('AccountAlreadyLinked')
            else:
                raise commands.CheckFailure('UserAlreadyVerified')

    @verify.command(brief='Allows user to link their account to a record in the database')
    async def basic(self, ctx, section: str, roll_no: int):
        # Gets the record of the given roll number
        self.c.execute('SELECT Section, Subsection, Name, Discord_UID, Guilds from main where Roll_Number = (:roll)', {'roll': roll_no})
        tuple = self.c.fetchone()
        # Exit if roll number doesn't exist
        if not tuple:
            await ctx.reply('The requested record was not found. Please re-check the entered details and try again')
            return
        # Exit if entered section doesn't match an existing section
        if section not in self.sections:
            await ctx.reply(f'\'{section}\' is not an existing section. Please re-check the entered details and try again')
            return
        # Exit if entered section doesn't match the section that the roll number is bound to
        if section != tuple[0]:
            await ctx.reply('The section that you entered does not match that of the roll number that you entered. Please re-check the entered details and try again')
            return
        # Exit if the record is already claimed by another user
        if user := self.bot.get_user(tuple[3]):
            await ctx.reply(f'The details you entered is of a record already claimed by `{user}`. If you think this was a mistake, contact a moderator.')
            return
        # Assigning one SubSection and one Section role to the user
        role = discord.utils.get(ctx.guild.roles, name=tuple[0])
        await ctx.author.add_roles(role)
        role = discord.utils.get(ctx.guild.roles, name=tuple[1])
        await ctx.author.add_roles(role)
        await ctx.reply('Your record was found and verified!\nPlease check the channel list of the server to see the unlocked channels. If you still do not see the channels then please re-launch the app.')
        # Removing the 'Not-Verified' role from the user
        role = discord.utils.get(ctx.guild.roles, name = 'Not-Verified')
        await ctx.author.remove_roles(role)
        # Fetches the mutual guilds list from the user
        guilds = json.loads(tuple[4])
        # Adds the new guild id if it is a new one
        if ctx.guild.id not in guilds:
            guilds.append(ctx.guild.id)
        guilds = json.dumps(guilds)
        # Updating the record in the database
        self.c.execute('UPDATE main SET Discord_UID = (:uid), Guilds = (:guilds) WHERE Roll_Number = (:roll)', {'uid': ctx.author.id, 'roll': roll_no, 'guilds': guilds})
        self.conn.commit()
        # Changing the nick of the user to their first name
        word = tuple[2].split(' ')[0]
        await ctx.author.edit(nick = word[:1] + word[1:].lower())

    @verify.command(brief='Allows user to verify their email')
    @commands.check(basicVerificationCheck)
    async def email(self, ctx, email: str):
        self.c.execute('SELECT Name, Institute_Email from main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()

        if email.lower() != tuple[1]:
            await ctx.reply('The email that you entered does not match your institute email. Please try again with a valid email.\nIf you think this was a mistake, contact a moderator.')
            return

        await ctx.message.add_reaction(self.emojis['loading'])

        # Setting variables for the email
        EMAIL = os.getenv('EMAIL')
        PASSWORD = os.getenv('PASSWORD')
        name = tuple[0].capitalize().strip()
        otp = self.generateotp()

        # Creating the email
        msg = EmailMessage()
        msg['Subject'] = f'Verification of {ctx.author} on {ctx.guild}'
        msg['From'] = EMAIL
        msg['To'] = tuple[1]
        msg.set_content(
            f'{self.string1}{name}{self.string2}{otp}{self.string3}
            {ctx.guild}{self.string4}{otp}{self.string5}',
            subtype='html'
        )

        # Sending the email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)

        await ctx.reply(f'Please check your institute email for the OTP and enter it here using `{ctx.prefix}verify code [OTP here]`.')
        await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)

        self.data[str(ctx.author.id)] = otp
        self.save()

    @verify.command(brief='Used to input OTP that the user received in order to verify their email')
    @commands.check(basicVerificationCheck)
    async def code(self, ctx, code: str):
        if str(ctx.author.id) not in self.data:
            await ctx.reply('You did not receive any email yet.')
            return

        if self.data[str(ctx.author.id)] == code:
            # Deletes the code
            del self.data[str(ctx.author.id)]
            self.save()

            # Marks user as verified in the database
            self.c.execute('UPDATE main SET Verified = "True" where Discord_UID = (:uid)', {'uid': ctx.author.id})
            self.conn.commit()

            await ctx.reply(f"Your email has been verified successfully! {self.emojis['verified']}")
        else:
            await ctx.reply('The code you entered is incorrect.')

    def save(self):
        with open('db/codes.json', 'w') as f:
            json.dump(self.data, f)

def setup(bot):
    bot.add_cog(Verify(bot))

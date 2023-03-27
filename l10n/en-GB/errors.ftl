UnhandledError = Something went wrong on our end! We're looking into it. Sorry for the inconvenience :(

BadRequest-otp = `{$OTP}` is incorrect. Please try again with the correct OTP.
IncorrectGuildBatch = This server is only for the { NUMBER($server_batch, useGrouping: 0) } batch. Since you're of the { NUMBER($student_batch, useGrouping: 0) } batch, you're (`{$roll}`) not allowed access on this server.

BatchNotFound = No data was found for the `{ NUMBER($batch, useGrouping: 0) }` batch.
RollNotFound = `{$roll_number}` was not found in our database. Please try again with a correct roll number. If you think this was a mistake, contact a moderator.

UserAlreadyVerified = You are already verified.
UserNotFound = {$member} does not exist in the database.
UserNotVerified = Only members with a verified email can use this command. To verify, simply type `/verify` and enter your roll number.

OTPTimeout = You took too long to enter the OTP, {$author}. Please restart the process to verify again.

Unauthorised-profile = You are not authorised to view the profiles of other users.
NotForBot = This command cannot be used for bot accounts!
NotOwner = This command is for the bot owner(s) only.

UserInputError-MissingRequiredArgument = '{$arg}' is a required argument that is missing.

CheckFailure-MissingAnyRole = You are missing at least one of the required roles: {$roles}

CommandInvokeError-Forbidden = I am missing some permissions to execute this command.

MaxConcurrencyReached = Please complete the steps of your previous command first! You cannot use this command more than once simulaneously.

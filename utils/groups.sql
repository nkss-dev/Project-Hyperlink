CREATE TABLE IF NOT EXISTS groups (
    name             text        primary key,
    alias            text        unique,
    faculty_advisor  text,
    mobile           varchar(14) unique,
    branch           varchar(5)  unique,
    kind             text        check(kind in ('cultural club', 'technical club', 'technical society')),
    description      text
);

CREATE TABLE IF NOT EXISTS group_discord (
    name            text        references groups(name),
    id              bigint      unique,
    invite          varchar(10) unique,
    fresher_role    bigint      unique,
    sophomore_role  bigint      unique,
    junior_role     bigint      unique,
    senior_role     bigint      unique,
    guest_role      bigint      unique
);

CREATE TABLE IF NOT EXISTS group_social (
    name  text references groups(name),
    type  varchar(15),
    link  text
);

CREATE TABLE IF NOT EXISTS group_admin (
    group_name   text references groups(name),
    position     varchar(20),
    roll_number  int  references student(roll_number)
);

CREATE TABLE IF NOT EXISTS group_member (
    roll_number  int  not null references student(roll_number),
    group_name   text not null references groups(name),
    primary key(roll_number, group_name)
);

CREATE OR REPLACE VIEW group_discord_user AS
    SELECT student.batch, student.discord_uid,
        c.name, c.alias, d.id, d.invite,
        d.fresher_role, d.sophomore_role, d.junior_role, d.senior_role,
        d.guest_role
        FROM group_member m
        JOIN groups c ON c.name = m.group_name
        JOIN group_discord d ON d.name = m.group_name
        JOIN student ON student.roll_number = m.roll_number
        WHERE student.discord_uid IS NOT NULL;

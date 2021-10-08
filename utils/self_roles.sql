create table if not exists views (
    Channel_ID int,
    Message_ID int unique,
    View_Type int default 0
);

create table if not exists buttons (
    Button_ID text primary key,
    Label text not null,
    Emoji text,
    Role_IDs text not null,
    Message_ID text not null,
    foreign key(Message_ID) references views(Message_ID) on update cascade
);

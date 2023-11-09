CREATE USER IF NOT EXISTS 'prospring5'@'localhost' IDENTIFIED BY 'prospring5';

DROP DATABASE IF EXISTS BOOK_MVC;
CREATE DATABASE BOOK_MVC;
USE BOOK_MVC;
GRANT ALL PRIVILEGES ON BOOK_MVC.* TO 'prospring5'@'localhost';
FLUSH PRIVILEGES;

/*in case of java.sql.SQLException: The server timezone value 'UTC' is unrecognized or represents more than one timezone. */
SET GLOBAL time_zone = '+5:00';
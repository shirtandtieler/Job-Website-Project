DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

-- Database: job_website_project
-- Intended for Postgres
-- Assumes execution in an empty database; requires plpgsql

-- Initialize enum types
CREATE TYPE skill_types AS ENUM('tech','biz');
CREATE TYPE account_types AS ENUM('Seeker', 'Company', 'Admin');
CREATE TYPE skill_levels AS ENUM('1','2','3','4','5');
	COMMENT ON TYPE skill_levels IS '1=familiar,5=expert';
CREATE TYPE importance_levels AS ENUM('1','2','3','4','5','6','7');
	COMMENT ON TYPE importance_levels IS '1=required,4=preferred,7=optional';

CREATE SEQUENCE Attitude_seq;
CREATE TABLE IF NOT EXISTS Attitude (
  id int CHECK (id > 0) NOT NULL DEFAULT NEXTVAL ('Attitude_seq'),
  title varchar(191) NOT NULL ,
  PRIMARY KEY (id),
  CONSTRAINT UC_Attitude_Title UNIQUE (title)
);

CREATE SEQUENCE Skill_seq;
CREATE TABLE IF NOT EXISTS Skill (
  id int CHECK (id > 0) NOT NULL DEFAULT NEXTVAL ('Skill_seq'),
  title varchar(191) NOT NULL,
  type skill_types NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT UC_Skill_Title UNIQUE (title)
);

CREATE SEQUENCE UserAccount_seq;
CREATE TABLE IF NOT EXISTS UserAccount (
  id int CHECK (id > 0) NOT NULL DEFAULT NEXTVAL ('UserAccount_seq'),
  account_type account_types NOT NULL,
  email varchar(191) NOT NULL,
  password varchar(191) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT UC_UserAccount_Email UNIQUE (email)
);
COMMENT ON COLUMN UserAccount.email IS 'login email';
COMMENT ON TABLE UserAccount IS 'Base table for *all* users (seekers, companies, and admins)';

CREATE TABLE IF NOT EXISTS UserActivity (
	user_id INT CHECK (user_id > 0) NOT NULL,
	is_active BOOLEAN NOT NULL DEFAULT TRUE,
	join_date TIMESTAMP(0) NOT NULL DEFAULT CURRENT_TIMESTAMP,
	last_login TIMESTAMP(0) NOT NULL DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT UC_UserActivity_UserID UNIQUE (user_id),
	CONSTRAINT FK_UserActivity_UserID FOREIGN KEY (user_id) REFERENCES UserAccount(id)
);
COMMENT ON TABLE UserActivity IS 'Log for basic activity for each type of user';

-- Trigger automatically fills in initial activity when an account is added
CREATE OR REPLACE FUNCTION add_new_activity() RETURNS TRIGGER AS
$$
BEGIN
	INSERT INTO UserActivity (user_id) VALUES (NEW.id);
	RETURN NEW;
END;
$$ LANGUAGE PLPGSQL;
CREATE TRIGGER record_initial_activity AFTER INSERT ON UserAccount FOR EACH ROW EXECUTE PROCEDURE add_new_activity();


CREATE TABLE IF NOT EXISTS CompanyProfile (
  company_id int CHECK (company_id > 0) NOT NULL,
  company_name varchar(191) DEFAULT NULL,
  city varchar(191) DEFAULT NULL,
  state_abbv varchar(2) DEFAULT NULL,
  zip_code varchar(5) DEFAULT NULL,
  website varchar(191) DEFAULT NULL,
  CONSTRAINT UC_CompanyProfile_ID UNIQUE (company_id),
  CONSTRAINT FK_CompanyProfile_ID FOREIGN KEY (company_id) REFERENCES UserAccount(id)
);

-- Trigger validates that the profile created for an account matches its respective account type;
-- The following function as part of triggers in Company and Seeker Profile.
-- Note: Arguments are accessed via TG_ARGV because you can't have parameters to a trigger function.
CREATE OR REPLACE FUNCTION validate_account() RETURNS TRIGGER AS
$$
DECLARE
	type_id_col text := TG_ARGV[0];
	required_type text := TG_ARGV[1];
	this_account text;
BEGIN
	EXECUTE format('SELECT account_type FROM UserAccount where id=NEW.%s', type_id_col) INTO this_account;
	IF (this_account) <> required_type
          THEN
               RAISE EXCEPTION 'User cannot be added to seeker table; user is not a %', required_type;
          END IF;
	RETURN NEW;
END;
$$ LANGUAGE PLPGSQL;

CREATE TRIGGER do_validate_company_account BEFORE INSERT ON CompanyProfile FOR EACH ROW EXECUTE PROCEDURE validate_account("company_id", "Company");

CREATE TABLE IF NOT EXISTS SeekerProfile (
  seeker_id int CHECK (seeker_id > 0) NOT NULL,
  contact_email varchar(191) NOT NULL,
  first_name varchar(191) DEFAULT NULL,
  last_name varchar(191) DEFAULT NULL,
  contact_phone int DEFAULT NULL,
  city varchar(191) DEFAULT NULL,
  state_abbv varchar(2) DEFAULT NULL,
  zip_code varchar(5) DEFAULT NULL,
  CONSTRAINT UC_SeekerProfile_ID UNIQUE (seeker_id),
  CONSTRAINT FK_SeekerProfile_ID FOREIGN KEY (seeker_id) REFERENCES UserAccount(id)
) ;

CREATE TRIGGER do_validate_seeker_account BEFORE INSERT ON SeekerProfile FOR EACH ROW EXECUTE PROCEDURE validate_account("seeker_id", "Seeker");

CREATE SEQUENCE SeekerHistoryEducation_seq;
CREATE TABLE IF NOT EXISTS SeekerHistoryEducation (
  id int CHECK (id > 0) NOT NULL DEFAULT NEXTVAL ('SeekerHistoryEducation_seq'),
  seeker_id int CHECK (seeker_id > 0) NOT NULL,
  education_level varchar(191) NOT NULL,
  study_field varchar(191) NOT NULL,
  school varchar(191) DEFAULT NULL,
  city varchar(191) DEFAULT NULL,
  state_abbv varchar(2) DEFAULT NULL,
  active_enrollment smallint DEFAULT NULL,
  start_date date DEFAULT NULL,
  end_date date DEFAULT NULL,
  PRIMARY KEY (id),
  CONSTRAINT FK_SeekerHistoryEducation_ID FOREIGN KEY (seeker_id) REFERENCES SeekerProfile(seeker_id)
) ;

CREATE SEQUENCE SeekerHistoryJob_seq;
CREATE TABLE IF NOT EXISTS SeekerHistoryJob (
  id int CHECK (id > 0) NOT NULL DEFAULT NEXTVAL ('SeekerHistoryJob_seq'),
  seeker_id int CHECK (seeker_id > 0) NOT NULL,
  job_title varchar(191) NOT NULL,
  company varchar(191) DEFAULT NULL,
  city varchar(191) DEFAULT NULL,
  state_abbv varchar(2) DEFAULT NULL,
  active_employment smallint DEFAULT NULL,
  start_date date DEFAULT NULL,
  end_date date DEFAULT NULL,
  PRIMARY KEY (id),
  CONSTRAINT FK_SeekerHistoryJob_ID FOREIGN KEY (seeker_id) REFERENCES SeekerProfile(seeker_id)
) ;

CREATE TABLE IF NOT EXISTS SeekerSkill (
  seeker_id int CHECK (seeker_id > 0) NOT NULL,
  skill_id int CHECK (skill_id > 0) NOT NULL,
  skill_level skill_levels NOT NULL,
  CONSTRAINT FK_SeekerSkill_SeekerID FOREIGN KEY (seeker_id) REFERENCES SeekerProfile(seeker_id),
  CONSTRAINT FK_SeekerSkill_SkillID FOREIGN KEY (skill_id) REFERENCES Skill(id),
  CONSTRAINT UC_SeekerSkill UNIQUE (seeker_id,skill_id)
);
COMMENT ON COLUMN SeekerSkill.skill_level IS '1=familiar,5=expert';

CREATE TABLE IF NOT EXISTS SeekerAttitude (
  seeker_id int CHECK (seeker_id > 0) NOT NULL,
  attitude_id int CHECK (attitude_id > 0) NOT NULL,
  CONSTRAINT FK_SeekerAttitude_SeekerID FOREIGN KEY (seeker_id) REFERENCES SeekerProfile(seeker_id),
  CONSTRAINT FK_SeekerAttitude_AttitudeID FOREIGN KEY (attitude_id) REFERENCES Attitude(id),
  CONSTRAINT UC_SeekerAttitude UNIQUE (seeker_id,attitude_id)
);

CREATE SEQUENCE JobPost_seq;
CREATE TABLE IF NOT EXISTS JobPost (
	id int CHECK (id > 0) NOT NULL DEFAULT NEXTVAL ('JobPost_seq'),
	company_id int CHECK (company_id > 0) NOT NULL,
	job_title varchar(191) NOT NULL,
	is_remote BOOLEAN DEFAULT NULL,
	city varchar(191) DEFAULT NULL,
	state_abbv varchar(2) DEFAULT NULL,
	description text DEFAULT NULL,
	PRIMARY KEY (id),
	CONSTRAINT FK_JobPost_CompanyID FOREIGN KEY (company_id) REFERENCES CompanyProfile(company_id)
);

CREATE SEQUENCE JobPostSkill_seq;
CREATE TABLE IF NOT EXISTS JobPostSkill (
	id int CHECK (id > 0) NOT NULL DEFAULT NEXTVAL ('JobPostSkill_seq'),
	jobpost_id int CHECK (jobpost_id > 0) NOT NULL,
	skill_id int CHECK (skill_id > 0) NOT NULL,
	skill_level_min skill_levels NOT NULL,
	importance_level importance_levels NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT FK_JobPostSkill_JobPostID FOREIGN KEY (jobpost_id) REFERENCES JobPost(id),
	CONSTRAINT FK_JobPostSkill_SkillID FOREIGN KEY (skill_id) REFERENCES Skill(id)
);
COMMENT ON COLUMN JobPostSkill.skill_level_min IS '1=familiar,5=expert';
COMMENT ON COLUMN JobPostSkill.importance_level IS '1=required,4=preferred,7=optional';

CREATE SEQUENCE JobPostAttitude_seq;
CREATE TABLE IF NOT EXISTS JobPostAttitude (
	id int CHECK (id > 0) NOT NULL DEFAULT NEXTVAL ('JobPostAttitude_seq'),
	jobpost_id int CHECK (jobpost_id > 0) NOT NULL,
	attitude_id int CHECK (attitude_id > 0) NOT NULL,
	importance_level importance_levels NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT FK_JobPostAttitude_JobPostID FOREIGN KEY (jobpost_id) REFERENCES JobPost(id),
	CONSTRAINT FK_JobPostAttitude_AttitudeID FOREIGN KEY (attitude_id) REFERENCES Attitude(id)
);
COMMENT ON COLUMN JobPostAttitude.importance_level IS '1=required,4=preferred,7=optional';

INSERT INTO Attitude (id, title) VALUES
(1, 'Shared ideals'),
(2, 'Collaborative work'),
(3, 'Individualized work'),
(4, 'Competitive work'),
(5, 'Teamwork focus'),
(6, 'Policy/procedure driven'),
(7, 'Structured environment'),
(8, 'Dynamic environment'),
(9, 'Risk-conscious'),
(10, 'Risk-oriented'),
(11, 'Outcome focus'),
(12, 'Lighthearted environment'),
(13, 'Innovative work'),
(14, 'Market driven goals'),
(15, 'Supportive environment'),
(16, 'Hierarchical structure'),
(17, 'Customer focus'),
(18, 'Quality driven'),
(19, 'Quantity driven'),
(20, 'Cost-consciousness'),
(21, 'Entrepreneurial spirit'),
(22, 'Personal accountability'),
(23, 'Group accountability'),
(24, 'Global accountability'),
(25, 'Sustainable work'),
(26, 'Ethics over profit');

INSERT INTO Skill (id, title, type) VALUES
(1, 'C/C++', 'tech'),
(2, 'C#', 'tech'),
(3, 'Java', 'tech'),
(4, 'JavaScript', 'tech'),
(5, 'Perl', 'tech'),
(6, 'PHP', 'tech'),
(7, 'Python', 'tech'),
(8, 'Swift', 'tech'),
(9, 'Go', 'tech'),
(10, 'SQL', 'tech'),
(11, 'R', 'tech'),
(12, 'Ruby', 'tech'),
(13, 'HTML', 'tech'),
(14, 'Git', 'tech'),
(15, 'Google Suite', 'tech'),
(16, 'Trello', 'tech'),
(17, 'Slack', 'tech'),
(18, 'Zapier', 'tech'),
(19, 'JIRA', 'tech'),
(20, 'Salesforce', 'tech'),
(21, 'Adobe creative apps', 'tech'),
(22, 'Oracle Solaris', 'tech'),
(23, 'UNIX', 'tech'),
(24, 'Microsoft Windows Server', 'tech'),
(25, 'Amazon Web Services', 'tech'),
(26, 'Microsoft Azure', 'tech'),
(27, 'Google Cloud Platform', 'tech'),
(28, 'Oracle JDBC', 'tech'),
(29, 'Front-end development', 'tech'),
(30, 'Backend development', 'tech'),
(31, 'Mobile development', 'tech'),
(32, 'Cloud computing', 'tech'),
(33, 'Network structure and security', 'tech'),
(34, 'Network architecture', 'tech'),
(35, 'BI tools', 'tech'),
(36, 'Big Data', 'tech'),
(37, 'Data Analytics', 'tech'),
(38, 'Data Mining', 'tech'),
(39, 'Database Design', 'tech'),
(40, 'Database Management', 'tech'),
(41, 'Artificial Intelligence', 'tech'),
(42, 'Technical Support', 'tech'),
(43, 'Active Listening', 'biz'),
(44, 'Agile', 'biz'),
(45, 'Asset Management', 'biz'),
(46, 'Automated marketing software', 'biz'),
(47, 'Bookkeeping', 'biz'),
(48, 'Budget Planning', 'biz'),
(49, 'Business Analysis', 'biz'),
(50, 'Business Intelligence', 'biz'),
(51, 'Business Management', 'biz'),
(52, 'Business Storytelling', 'biz'),
(53, 'Conflict Management', 'biz'),
(54, 'Consulting', 'biz'),
(55, 'Content Management Systems (CMS)', 'biz'),
(56, 'Copywriting', 'biz'),
(57, 'Customer Relationship Management', 'biz'),
(58, 'Customer Service', 'biz'),
(59, 'Human Resources', 'biz'),
(60, 'Leadership Roles', 'biz'),
(61, 'Market Research', 'biz'),
(62, 'Nonverbal Communication', 'biz'),
(63, 'Presentation', 'biz'),
(64, 'Product Lifecycle Management', 'biz'),
(65, 'Product Management', 'biz'),
(66, 'Product Roadmaps', 'biz'),
(67, 'Project Management', 'biz'),
(68, 'Project Planning', 'biz'),
(69, 'Prototyping', 'biz'),
(70, 'Public Relations', 'biz'),
(71, 'Public Speaking', 'biz'),
(72, 'QA Testing', 'biz'),
(73, 'Quality Assurance', 'biz'),
(74, 'Quality Control', 'biz'),
(75, 'Quantitative Reports', 'biz'),
(76, 'Quantitative Research', 'biz'),
(77, 'Requirements Gathering', 'biz'),
(78, 'Risk management', 'biz'),
(79, 'Scheduling', 'biz'),
(80, 'SCRUM', 'biz'),
(81, 'Search Engine Optimization (SEO)', 'biz'),
(82, 'Task Delegation', 'biz'),
(83, 'Task Management', 'biz'),
(84, 'User Experience Design', 'biz'),
(85, 'User Interface Design', 'biz'),
(86, 'Verbal Communication', 'biz'),
(87, 'Web Analytics', 'biz'),
(88, 'Wireframing', 'biz'),
(89, 'Written Communication', 'biz');
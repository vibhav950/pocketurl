CREATE TABLE IF NOT EXISTS urls (
  counter INTEGER AUTO_INCREMENT PRIMARY KEY,
  long_url VARCHAR(1024) NOT NULL,
  short_url VARCHAR(255),
  hits INT DEFAULT 0
);


CREATE INDEX idx_counter ON urls(counter);
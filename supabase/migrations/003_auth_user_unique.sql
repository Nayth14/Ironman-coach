-- Unique auth identity per athlete (supports link-guest conflict detection)
CREATE UNIQUE INDEX IF NOT EXISTS idx_athletes_auth_user_id_unique
  ON athletes(auth_user_id)
  WHERE auth_user_id IS NOT NULL;

import { readdir, readFile, appendFile } from 'node:fs/promises'
import path from 'node:path'
import moment from 'moment'
const MIGRATION_LOCK_FILE_NAME = 'migration.lock'

export async function loadJson(filepath: string) {
  try {
    const json = await readFile(filepath, 'utf8')
    return JSON.parse(json)
  } catch (e) {
    console.error(e)
    throw e
  }
}

async function readMigrationLockFile(filePath: string) {
  return (await readFile(filePath, 'utf8')).toString().trim().split('\n')
}

/**
 * Migrations directory includes migration JSON files and migration lock file.
 * Migration JSON files should have a names that explains the
 * migration purpose and which can be chronological order. If there is
 * no migration lock file, we assume that no migration has been run
 * yet. `loadMigration` function examines migration JSON files,
 * migration lock file and determines which migration JSON files
 * should be used for next migration.
 *
 * @param {string} migrations directory
 * @return {Promise<string[]>} list of migration files names that has
 * not been applied yet
 */
export async function loadMigration(dirPath: string): Promise<string[]> {
  const jsonFileRegex = /\.json$/

  let migrationLockFileExist = false
  const allMigrations = []

  try {
    const files = await readdir(dirPath)

    for (const file of files) {
      if (file === MIGRATION_LOCK_FILE_NAME) {
        migrationLockFileExist = true
      } else if (jsonFileRegex.test(file.toLowerCase())) {
        allMigrations.push(file)
      }
    }
  } catch (err) {
    console.error(err)
  }

  let doneMigrations: any[] = []
  if (migrationLockFileExist) {
    const migrationLockFilePath = path.join(dirPath, MIGRATION_LOCK_FILE_NAME)
    doneMigrations = await readMigrationLockFile(migrationLockFilePath)
  }

  // Keep only those migrations that have not been applied yet
  const todoMigrations = allMigrations.filter((x) => !doneMigrations.includes(x))
  todoMigrations.sort()
  return todoMigrations
}

/**
 * Update migration lock file located in `dirPath` with the `migrationFileName` migration.
 *
 * @params {string} migration directory
 * @params {string} name of executed migration file that should be included to migration lock file
 * @return {Promise<void>}
 */
export async function updateMigration(dirPath: string, migrationFileName: string) {
  const migrationLockFilePath = path.join(dirPath, MIGRATION_LOCK_FILE_NAME)
  await appendFile(migrationLockFilePath, `${migrationFileName}\n`)
}

export function getFormattedDate() {
  return moment().format('YYYYMMDDHHMMSS')
}

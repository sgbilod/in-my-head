# 🚀 Quick Database Setup - No Password Required!

## Problem
You have PostgreSQL installed but don't know the `postgres` user password, and it's shared with other projects.

## Solution: Create Project User via pgAdmin (2 minutes)

### Step 1: Open pgAdmin
1. Search for "pgAdmin" in Windows Start menu
2. Open pgAdmin 4
3. It will connect to your local PostgreSQL server

### Step 2: Create New User
1. In pgAdmin, expand "Servers" → "PostgreSQL 14" → right-click "Login/Group Roles"
2. Select "Create" → "Login/Group Role..."
3. In the "General" tab:
   - Name: `inmyhead`
4. In the "Definition" tab:
   - Password: `inmyhead_dev_pass`
5. In the "Privileges" tab:
   - Enable: ✅ "Can login?"
   - Enable: ✅ "Create databases?"
6. Click "Save"

### Step 3: Create Database
1. Right-click "Databases" → "Create" → "Database..."
2. Database name: `inmyhead_dev`
3. Owner: `inmyhead` (select from dropdown)
4. Click "Save"

### Step 4: Run Migrations
Now open PowerShell in your project directory and run:

```powershell
cd "C:\Users\sgbil\In My Head\services\document-processor"

# Set the database connection
$env:DATABASE_URL = "postgresql://inmyhead:inmyhead_dev_pass@localhost:5432/inmyhead_dev"

# Run migrations
python -m alembic upgrade head

# Seed test data
python -m src.database.seed
```

### Step 5: Verify
```powershell
# Test connection
python -c "from src.database.connection import check_health; check_health()"
```

You should see: ✅ Success!

---

## Alternative: Use Docker (Completely Separate)

If you prefer to keep this project completely isolated:

### 1. Use a Different Port for Docker
Edit `infrastructure\docker\docker-compose.dev.yml` and change the PostgreSQL port:
```yaml
postgres:
  ports:
    - "5433:5432"  # Use 5433 instead of 5432
```

### 2. Start Docker PostgreSQL
```powershell
cd infrastructure\docker
docker-compose -f docker-compose.dev.yml up -d postgres
```

### 3. Run Migrations
```powershell
cd ..\..\services\document-processor

# Use the Docker database on port 5433
$env:DATABASE_URL = "postgresql://inmyhead:inmyhead_dev_pass_change_in_prod@localhost:5433/inmyhead_dev"

python -m alembic upgrade head
python -m src.database.seed
```

---

## What Gets Created

**Database User:**
- Username: `inmyhead`
- Password: `inmyhead_dev_pass`
- Database: `inmyhead_dev`

**Test Account (after seeding):**
- Username: `testuser`
- Password: `Test123!`
- Email: `test@inmyhead.local`

---

## Which Method Should You Use?

### Use pgAdmin Method If:
- ✅ You want to keep using your existing PostgreSQL
- ✅ You want a GUI and don't like command line
- ✅ You're comfortable with pgAdmin
- ✅ Other projects are already using port 5432

### Use Docker Method If:
- ✅ You want complete isolation from other projects
- ✅ You prefer command-line tools
- ✅ You want easy teardown/rebuild
- ✅ You don't mind Docker running

---

## Need Help?

If you get stuck, just let me know which method you chose and what error you're seeing! 🙂

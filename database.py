import os
import asyncio
import logging
from typing import Optional
import aiomysql
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool: Optional[aiomysql.Pool] = None

    async def connect(self):
        """连接到MySQL数据库"""
        try:
            db_url = os.getenv('DB_MYSQL')
            if not db_url:
                raise ValueError("DB_MYSQL environment variable is required")
            
            # 解析数据库连接字符串格式: mysql://user:password@host:port/database
            if db_url.startswith('mysql://'):
                db_url = db_url[8:]
            
            parts = db_url.split('@')
            if len(parts) != 2:
                raise ValueError("Invalid DB_MYSQL format. Expected: mysql://user:password@host:port/database")
            
            user_pass = parts[0].split(':')
            host_db = parts[1].split('/')
            if len(user_pass) != 2 or len(host_db) != 2:
                raise ValueError("Invalid DB_MYSQL format. Expected: mysql://user:password@host:port/database")
            
            user, password = user_pass
            host_port, database = host_db
            
            host_parts = host_port.split(':')
            host = host_parts[0]
            port = int(host_parts[1]) if len(host_parts) > 1 else 3306
            
            self.pool = await aiomysql.create_pool(
                host=host,
                port=port,
                user=user,
                password=password,
                db=database,
                minsize=1,
                maxsize=10,
                autocommit=True
            )
            
            logger.info("MySQL connection pool created successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {e}")
            raise

    async def disconnect(self):
        """关闭数据库连接"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("MySQL connection pool closed")

    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接上下文管理器"""
        if not self.pool:
            await self.connect()
        
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            self.pool.release(conn)

    async def execute(self, query: str, *args):
        """执行SQL查询"""
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, args)
                return cursor

    async def initialize_database(self):
        """初始化数据库表结构"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS accounts (
            email VARCHAR(255) PRIMARY KEY,
            refresh_token TEXT NOT NULL,
            client_id VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_email (email),
            INDEX idx_updated_at (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        try:
            async with self.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(create_table_query)
                    logger.info("Accounts table created or already exists")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

# 全局数据库实例
db = Database()
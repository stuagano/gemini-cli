/**
 * Scaling Demo Scenarios - Demonstration code examples that showcase scaling issues
 * These examples are designed to trigger the scaling detector for demonstration purposes
 */

export const DEMO_SCENARIOS = {
  // N+1 Query Examples
  n_plus_one_examples: {
    bad_user_orders: `
// ❌ Classic N+1 Query - User Orders
async function getUsersWithOrders(userIds: string[]) {
  const users = await db.query('SELECT * FROM users WHERE id IN (?)', [userIds]);
  
  for (const user of users) {
    // This creates N additional queries!
    const orders = await db.query('SELECT * FROM orders WHERE user_id = ?', [user.id]);
    user.orders = orders;
  }
  
  return users;
}`,

    bad_product_reviews: `
// ❌ N+1 Query - Product Reviews
async function getProductsWithReviews() {
  const products = await Product.findAll();
  
  const enrichedProducts = products.map(async (product) => {
    // This executes one query per product!
    const reviews = await Review.findByProductId(product.id);
    const avgRating = await Review.getAverageRating(product.id);
    
    return {
      ...product,
      reviews,
      avgRating
    };
  });
  
  return Promise.all(enrichedProducts);
}`,

    bad_foreach_updates: `
// ❌ N+1 Query - Sequential Updates
async function updateUserStats(users: User[]) {
  users.forEach(async (user) => {
    // Each update is a separate query!
    await db.query(
      'UPDATE user_stats SET last_login = NOW() WHERE user_id = ?', 
      [user.id]
    );
  });
}`,

    good_batch_solution: `
// ✅ Optimized Solution - Batch Queries
async function getUsersWithOrdersOptimized(userIds: string[]) {
  // Single query for users
  const users = await db.query('SELECT * FROM users WHERE id IN (?)', [userIds]);
  
  // Single query for all orders
  const allOrders = await db.query('SELECT * FROM orders WHERE user_id IN (?)', [userIds]);
  
  // Group orders by user_id in memory (fast)
  const ordersByUserId = allOrders.reduce((acc, order) => {
    if (!acc[order.user_id]) acc[order.user_id] = [];
    acc[order.user_id].push(order);
    return acc;
  }, {});
  
  // Attach orders to users
  users.forEach(user => {
    user.orders = ordersByUserId[user.id] || [];
  });
  
  return users;
}`
  },

  // Memory Leak Examples
  memory_leak_examples: {
    bad_unclosed_connections: `
// ❌ Database Connection Leak
async function processLargeDataset(items: any[]) {
  for (const item of items) {
    const connection = await pool.getConnection();
    
    try {
      const result = await connection.query('INSERT INTO processed_items VALUES (?)', [item]);
      
      if (result.error) {
        throw new Error('Processing failed');
      }
    } catch (error) {
      console.error('Failed to process item:', error);
      // Connection never closed on error!
      return;
    }
    
    // Connection only closed on success path
    connection.release();
  }
}`,

    bad_event_listeners: `
// ❌ Event Listener Memory Leak
class DataProcessor {
  private listeners: Map<string, Function[]> = new Map();
  
  processFile(filePath: string) {
    const watcher = fs.watch(filePath);
    
    watcher.on('change', (eventType) => {
      this.handleFileChange(eventType, filePath);
    });
    
    // Listeners accumulate but are never removed!
    // Each file processing adds more listeners
  }
  
  handleFileChange(eventType: string, filePath: string) {
    console.log('File ' + filePath + ' changed: ' + eventType);
  }
}`,

    bad_global_cache: `
// ❌ Unbounded Global Cache Growth
const globalCache = {
  userSessions: new Map(),
  apiResponses: new Map(),
  calculations: new Map()
};

function cacheUserSession(userId: string, sessionData: any) {
  // Cache grows forever - never cleaned up!
  globalCache.userSessions.set(userId, {
    data: sessionData,
    timestamp: Date.now()
  });
}

function cacheApiResponse(url: string, response: any) {
  // This will eventually consume all memory
  globalCache.apiResponses.set(url, response);
}`,

    good_memory_management: `
// ✅ Proper Memory Management
async function processLargeDatasetSafe(items: any[]) {
  for (const item of items) {
    const connection = await pool.getConnection();
    
    try {
      const result = await connection.query('INSERT INTO processed_items VALUES (?)', [item]);
      
      if (result.error) {
        throw new Error('Processing failed');
      }
    } finally {
      // Always release connection, even on error
      connection.release();
    }
  }
}

// ✅ LRU Cache with Size Limits
import LRU from 'lru-cache';

const userSessionCache = new LRU({
  max: 10000, // Maximum 10k sessions
  ttl: 30 * 60 * 1000 // 30 minute TTL
});

const apiResponseCache = new LRU({
  max: 1000, // Maximum 1k cached responses
  ttl: 5 * 60 * 1000 // 5 minute TTL
});`
  },

  // Inefficient Algorithm Examples
  inefficient_algorithm_examples: {
    bad_nested_loops: `
// ❌ O(n²) Nested Loops - Find Matching Orders
function matchUsersWithOrders(users: User[], orders: Order[]) {
  const results = [];
  
  for (const user of users) {
    const userOrders = [];
    
    // Inner loop creates O(n²) complexity!
    for (const order of orders) {
      if (order.userId === user.id) {
        userOrders.push(order);
      }
    }
    
    results.push({
      user,
      orders: userOrders
    });
  }
  
  return results;
}`,

    bad_repeated_find: `
// ❌ Repeated Linear Search - O(n²) Behavior
function enrichUsersWithProfiles(users: User[], profiles: Profile[]) {
  return users.map(user => {
    // This creates O(n²) because find() is O(n) and we do it n times!
    const profile = profiles.find(p => p.userId === user.id);
    
    return {
      ...user,
      profile: profile || null
    };
  });
}`,

    bad_expensive_calculations: `
// ❌ Repeated Expensive Calculations in Loop
function processTransactions(transactions: Transaction[]) {
  const results = [];
  
  for (const transaction of transactions) {
    // Expensive cryptographic operation repeated every iteration!
    const hash = crypto.createHash('sha256')
      .update(transaction.data)
      .digest('hex');
    
    // Complex calculation repeated
    const fee = calculateComplexFee(transaction.amount, transaction.type);
    
    results.push({
      ...transaction,
      hash,
      fee
    });
  }
  
  return results;
}`,

    good_efficient_algorithms: `
// ✅ O(n) Hash Map Solution
function matchUsersWithOrdersOptimized(users: User[], orders: Order[]) {
  // Build lookup map once - O(n)
  const ordersByUserId = orders.reduce((acc, order) => {
    if (!acc[order.userId]) acc[order.userId] = [];
    acc[order.userId].push(order);
    return acc;
  }, {} as Record<string, Order[]>);
  
  // Map users with O(1) lookup - Total O(n)
  return users.map(user => ({
    user,
    orders: ordersByUserId[user.id] || []
  }));
}

// ✅ Pre-compute Lookup Map
function enrichUsersWithProfilesOptimized(users: User[], profiles: Profile[]) {
  // Create lookup map once - O(n)
  const profilesByUserId = new Map(
    profiles.map(profile => [profile.userId, profile])
  );
  
  // Map with O(1) lookups - Total O(n)
  return users.map(user => ({
    ...user,
    profile: profilesByUserId.get(user.id) || null
  }));
}`
  },

  // Blocking Operations Examples
  blocking_operations_examples: {
    bad_sync_file_operations: `
// ❌ Synchronous File Operations Block Event Loop
function processConfigFiles(configDir: string) {
  const files = fs.readdirSync(configDir); // Blocks!
  
  const configs = files.map(file => {
    const filePath = path.join(configDir, file);
    
    if (fs.existsSync(filePath)) { // Blocks!
      const content = fs.readFileSync(filePath, 'utf-8'); // Blocks!
      return JSON.parse(content);
    }
    
    return null;
  }).filter(Boolean);
  
  return configs;
}`,

    bad_sync_network_calls: `
// ❌ Synchronous Network Calls (worst case!)
function fetchUserDataSync(userId: string) {
  const xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/users/' + userId, false); // Synchronous!
  xhr.send();
  
  if (xhr.status === 200) {
    return JSON.parse(xhr.responseText);
  }
  
  throw new Error('Failed to fetch user data');
}`,

    bad_cpu_intensive_sync: `
// ❌ CPU-Intensive Work Blocking Event Loop
function calculatePrimeNumbers(max: number): number[] {
  const primes: number[] = [];
  
  // This blocks the event loop for potentially minutes!
  for (let num = 2; num <= max; num++) {
    let isPrime = true;
    
    for (let i = 2; i <= Math.sqrt(num); i++) {
      if (num % i === 0) {
        isPrime = false;
        break;
      }
    }
    
    if (isPrime) {
      primes.push(num);
    }
  }
  
  return primes;
}`,

    good_async_operations: `
// ✅ Async File Operations
async function processConfigFilesAsync(configDir: string) {
  const files = await fs.promises.readdir(configDir);
  
  const configs = await Promise.all(
    files.map(async file => {
      const filePath = path.join(configDir, file);
      
      try {
        const content = await fs.promises.readFile(filePath, 'utf-8');
        return JSON.parse(content);
      } catch (error) {
        console.warn('Failed to read config file ' + file + ':', error);
        return null;
      }
    })
  );
  
  return configs.filter(Boolean);
}

// ✅ Worker Threads for CPU-Intensive Work
async function calculatePrimeNumbersAsync(max: number): Promise<number[]> {
  return new Promise((resolve, reject) => {
    const worker = new Worker('./prime-worker.js');
    
    worker.postMessage({ max });
    
    worker.on('message', (primes) => {
      worker.terminate();
      resolve(primes);
    });
    
    worker.on('error', (error) => {
      worker.terminate();
      reject(error);
    });
  });
}`
  },

  // Real-world Scaling Disaster Examples
  real_world_disasters: {
    social_media_feed: `
// ❌ Social Media Feed - Multiple Scaling Issues
async function generateUserFeed(userId: string, limit: number = 50) {
  // N+1 Query: Get user's followed accounts
  const user = await User.findById(userId);
  const followedUsers = [];
  
  for (const followId of user.following) {
    // N queries for followed users!
    const followedUser = await User.findById(followId);
    followedUsers.push(followedUser);
  }
  
  // N+1 Query: Get posts from each followed user
  const allPosts = [];
  for (const followedUser of followedUsers) {
    // N more queries for posts!
    const posts = await Post.findByUserId(followedUser.id);
    
    // N+1 again: Get like counts for each post
    for (const post of posts) {
      const likes = await Like.findByPostId(post.id); // N*M queries!
      post.likeCount = likes.length;
      
      // Memory leak: Event listeners never cleaned up
      post.addEventListener('like', this.handleLike.bind(this));
    }
    
    allPosts.push(...posts);
  }
  
  // Inefficient sorting - not using database
  allPosts.sort((a, b) => {
    // Expensive calculation repeated for every comparison!
    const scoreA = calculateEngagementScore(a);
    const scoreB = calculateEngagementScore(b);
    return scoreB - scoreA;
  });
  
  return allPosts.slice(0, limit);
}`,

    ecommerce_product_search: `
// ❌ E-commerce Product Search - Scaling Nightmare
async function searchProducts(query: string, filters: any) {
  // Synchronous file operation to read search config
  const searchConfig = JSON.parse(
    fs.readFileSync('./search-config.json', 'utf-8') // Blocks!
  );
  
  // N+1: Get all products then filter in application
  const allProducts = await Product.findAll();
  
  const results = [];
  for (const product of allProducts) {
    // Expensive text similarity calculation for every product!
    const similarity = calculateTextSimilarity(query, product.name);
    
    if (similarity > 0.3) {
      // N+1: Get category info for each matching product
      const category = await Category.findById(product.categoryId);
      
      // N+1: Get reviews for each product
      const reviews = await Review.findByProductId(product.id);
      
      // Inefficient algorithm: Linear search through all reviews
      const avgRating = reviews.reduce((sum, review) => sum + review.rating, 0) / reviews.length;
      
      // Memory leak: Cache grows without bounds
      global.searchCache = global.searchCache || {};
      global.searchCache[product.id] = {
        product,
        category,
        reviews,
        avgRating,
        timestamp: Date.now()
      };
      
      results.push({
        product,
        category,
        avgRating,
        similarity
      });
    }
  }
  
  // Inefficient sorting without database indexes
  return results.sort((a, b) => b.similarity - a.similarity);
}`
  },

  // Performance Testing Scenarios
  performance_test_scenarios: {
    load_test_setup: `
// Performance Test Scenarios for Scaling Demo
export const SCALING_LOAD_TESTS = {
  // Test N+1 query performance degradation
  async testNPlusOnePerformance() {
    const userCounts = [10, 50, 100, 500, 1000];
    const results = [];
    
    for (const userCount of userCounts) {
      const startTime = Date.now();
      
      // This will trigger N+1 detection
      const users = await getUsersWithOrders(Array(userCount).fill().map((_, i) => i));
      
      const duration = Date.now() - startTime;
      results.push({
        userCount,
        duration,
        avgTimePerUser: duration / userCount
      });
      
      console.log(userCount + ' users: ' + duration + 'ms (' + (duration/userCount) + 'ms per user)');
    }
    
    return results;
  },
  
  // Test memory leak detection
  async testMemoryLeakDetection() {
    const iterations = [100, 500, 1000, 5000];
    const results = [];
    
    for (const iterCount of iterations) {
      const startMemory = process.memoryUsage().heapUsed;
      
      // This will trigger memory leak detection
      for (let i = 0; i < iterCount; i++) {
        await processWithConnectionLeak(i);
      }
      
      const endMemory = process.memoryUsage().heapUsed;
      const memoryGrowth = endMemory - startMemory;
      
      results.push({
        iterations: iterCount,
        memoryGrowthMB: memoryGrowth / 1024 / 1024,
        memoryPerOperation: memoryGrowth / iterCount
      });
    }
    
    return results;
  }
};`
  }
};

export const DEMO_FILES = {
  'bad-n-plus-one.ts': DEMO_SCENARIOS.n_plus_one_examples.bad_user_orders,
  'bad-memory-leak.ts': DEMO_SCENARIOS.memory_leak_examples.bad_unclosed_connections,
  'bad-algorithms.ts': DEMO_SCENARIOS.inefficient_algorithm_examples.bad_nested_loops,
  'bad-blocking-ops.ts': DEMO_SCENARIOS.blocking_operations_examples.bad_sync_file_operations,
  'scaling-disaster.ts': DEMO_SCENARIOS.real_world_disasters.social_media_feed
};

/**
 * Generate demonstration files for testing the scaling detector
 */
export async function createDemoFiles(outputDir: string = './demo-scenarios'): Promise<void> {
  const fs = await import('fs/promises');
  const path = await import('path');
  
  try {
    await fs.mkdir(outputDir, { recursive: true });
    
    for (const [filename, content] of Object.entries(DEMO_FILES)) {
      const filePath = path.join(outputDir, filename);
      await fs.writeFile(filePath, content, 'utf-8');
      console.log('Created demo file: ' + filePath);
    }
    
    console.log('\\n✅ Created ' + Object.keys(DEMO_FILES).length + ' demo scenario files in ' + outputDir);
    
  } catch (error) {
    console.error('Failed to create demo files:', error);
    throw error;
  }
}

export default DEMO_SCENARIOS;
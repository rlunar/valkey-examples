local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local request_id = ARGV[3]

-- Reject invalid settings before changing the sorted set.
if not limit or limit < 1 then
    return redis.error_reply("limit must be a positive integer")
end
if not window_ms or window_ms < 1 then
    return redis.error_reply("window_ms must be a positive integer")
end
if not request_id or request_id == "" then
    return redis.error_reply("request_id must not be empty")
end

-- Use Valkey's clock so every application server agrees on the time.
local server_time = redis.call("TIME")
local now_ms = (tonumber(server_time[1]) * 1000) + math.floor(tonumber(server_time[2]) / 1000)
local cutoff_ms = now_ms - window_ms

-- Remove requests that are no longer inside the sliding window.
redis.call("ZREMRANGEBYSCORE", key, "-inf", cutoff_ms)

-- Accept only when the current number of requests is below the limit.
local active_count = redis.call("ZCARD", key)
local allowed = 0

if active_count < limit then
    -- The request ID prevents two requests in the same millisecond from
    -- replacing each other.
    local member = tostring(now_ms) .. ":" .. request_id
    redis.call("ZADD", key, now_ms, member)
    redis.call("PEXPIRE", key, window_ms)
    active_count = active_count + 1
    allowed = 1
end

-- The oldest remaining request tells the caller when space will open.
local oldest = redis.call("ZRANGE", key, 0, 0, "WITHSCORES")
local oldest_ms = now_ms
if #oldest >= 2 then
    oldest_ms = tonumber(oldest[2])
end

local reset_after_ms = math.max(0, oldest_ms + window_ms - now_ms)
local remaining = math.max(0, limit - active_count)
local retry_after_ms = 0
if allowed == 0 then
    retry_after_ms = math.max(1, reset_after_ms)
end

-- Return the same five fields as the transaction implementation.
return {allowed, limit, remaining, reset_after_ms, retry_after_ms}

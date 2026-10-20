#!/usr/bin/env bash

set -euo pipefail

state_file="${WEATHER_STATE_FILE:-${XDG_STATE_HOME:-$HOME/.local/state}/desktop-bar/weather.json}"
cache_file="${WEATHER_CACHE_FILE:-${XDG_CACHE_HOME:-$HOME/.cache}/desktop-bar-weather.json}"
cache_ttl_seconds=900
location_key="auto"
if [[ -r "$state_file" ]]; then
  location_key="$(sha256sum "$state_file" | awk '{print $1}')"
fi
cache_source="open-meteo-v4-${location_key}"

round_number() {
  awk -v n="${1:-}" 'BEGIN { if (n == "" || n == "null") print "--"; else printf "%.0f", n }'
}

weather_icon() {
  local code="${1:-}" is_day="${2:-1}"
  case "$code" in
    0) [[ "$is_day" == "0" ]] && printf '' || printf '' ;;
    1|2) [[ "$is_day" == "0" ]] && printf '' || printf '' ;;
    3) printf '' ;;
    45|48) [[ "$is_day" == "0" ]] && printf '\ue346' || printf '\ue313' ;;
    51|53|55|56|57|61) [[ "$is_day" == "0" ]] && printf '' || printf '' ;;
    63|65|66|67|80|81|82) printf '' ;;
    71|73|75|77|85|86) printf '' ;;
    95|96|99) printf '' ;;
    *) printf '' ;;
  esac
}

condition_text() {
  case "${1:-}" in
    0) printf 'Clear' ;;
    1) printf 'Mainly clear' ;;
    2) printf 'Partly cloudy' ;;
    3) printf 'Overcast' ;;
    45|48) printf 'Fog' ;;
    51|53|55) printf 'Drizzle' ;;
    56|57) printf 'Freezing drizzle' ;;
    61|63|65) printf 'Rain' ;;
    66|67) printf 'Freezing rain' ;;
    71|73|75) printf 'Snow' ;;
    77) printf 'Snow grains' ;;
    80|81|82) printf 'Rain showers' ;;
    85|86) printf 'Snow showers' ;;
    95) printf 'Thunderstorm' ;;
    96|99) printf 'Thunderstorm with hail' ;;
    *) printf 'Current conditions' ;;
  esac
}

cache_is_fresh() {
  [[ -r "$cache_file" ]] || return 1
  local cache_mtime now source
  cache_mtime="$(stat -c %Y "$cache_file" 2>/dev/null || echo 0)"
  now="$(date +%s)"
  ((now - cache_mtime < cache_ttl_seconds)) || return 1
  source="$(jq -r '.source // empty' "$cache_file" 2>/dev/null || true)"
  [[ "$source" == "$cache_source" ]]
}

if [[ "${WEATHER_FORCE_REFRESH:-0}" != "1" ]] && cache_is_fresh; then
  cat "$cache_file"
  exit 0
fi

name=""
lat=""
lon=""

if [[ -r "$state_file" ]]; then
  name="$(jq -r '.name // empty' "$state_file" 2>/dev/null || true)"
  lat="$(jq -r '.latitude // empty' "$state_file" 2>/dev/null || true)"
  lon="$(jq -r '.longitude // empty' "$state_file" 2>/dev/null || true)"
fi

if [[ -n "$name" && (-z "$lat" || -z "$lon") ]]; then
  encoded_name="$(jq -rn --arg q "$name" '$q|@uri')"
  geocode="$(curl --max-time 5 --silent --show-error --fail "https://geocoding-api.open-meteo.com/v1/search?count=1&language=en&format=json&name=${encoded_name}" 2>/dev/null || true)"
  lat="$(jq -r '.results[0].latitude // empty' <<<"$geocode" 2>/dev/null || true)"
  lon="$(jq -r '.results[0].longitude // empty' <<<"$geocode" 2>/dev/null || true)"
  resolved="$(jq -r '.results[0] | [.name, .country] | map(select(. != null and . != "")) | join(", ")' <<<"$geocode" 2>/dev/null || true)"
  [[ -n "$resolved" ]] && name="$resolved"
fi

if [[ -z "$lat" || -z "$lon" ]]; then
  wttr="$(curl --max-time 5 --silent --show-error --fail "https://wttr.in/?format=j1" 2>/dev/null || true)"
  lat="$(jq -r '.nearest_area[0].latitude // empty' <<<"$wttr" 2>/dev/null || true)"
  lon="$(jq -r '.nearest_area[0].longitude // empty' <<<"$wttr" 2>/dev/null || true)"
  area="$(jq -r '.nearest_area[0].areaName[0].value // empty' <<<"$wttr" 2>/dev/null || true)"
  country="$(jq -r '.nearest_area[0].country[0].value // empty' <<<"$wttr" 2>/dev/null || true)"
  name="$(jq -rn --arg area "$area" --arg country "$country" '[$area,$country] | map(select(. != "")) | join(", ")')"
fi

if [[ -z "$lat" || -z "$lon" ]]; then
  if [[ -r "$cache_file" ]]; then
    cat "$cache_file"
  else
    jq -cn --arg source "$cache_source" '{source:$source,text:" --",location:"Weather",condition:"Unavailable",temp:"--",feels:"--",wind:"--",humidity:"--",forecast:"--",forecastDays:[]}'
  fi
  exit 0
fi

unit_args="&temperature_unit=celsius&wind_speed_unit=kmh"
unit_suffix="°C"
wind_suffix="km/h"
if [[ -r "$state_file" ]]; then
  country_code="$(jq -r '.country_code // empty' "$state_file")"
  case "$country_code" in
    US|LR|MM)
      unit_args="&temperature_unit=fahrenheit&wind_speed_unit=mph"
      unit_suffix="°F"
      wind_suffix="mph"
      ;;
  esac
fi

url="https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code,is_day&daily=weather_code,temperature_2m_max,temperature_2m_min&forecast_days=4&timezone=auto${unit_args}"
raw="$(curl --max-time 5 --silent --show-error --fail "$url" 2>/dev/null || true)"

if [[ -z "$raw" ]]; then
  if [[ -r "$cache_file" ]]; then
    cat "$cache_file"
  else
    jq -cn --arg source "$cache_source" '{source:$source,text:" --",location:"Weather",condition:"Unavailable",temp:"--",feels:"--",wind:"--",humidity:"--",forecast:"--",forecastDays:[]}'
  fi
  exit 0
fi

code="$(jq -r '.current.weather_code // empty' <<<"$raw")"
is_day="$(jq -r '.current.is_day // 1' <<<"$raw")"
temp_num="$(round_number "$(jq -r '.current.temperature_2m // empty' <<<"$raw")")"
feels_num="$(round_number "$(jq -r '.current.apparent_temperature // empty' <<<"$raw")")"
humidity="$(round_number "$(jq -r '.current.relative_humidity_2m // empty' <<<"$raw")")"
wind_num="$(round_number "$(jq -r '.current.wind_speed_10m // empty' <<<"$raw")")"
forecast="$(round_number "$(jq -r '.daily.temperature_2m_max[1] // empty' <<<"$raw")")°"

icon="$(weather_icon "$code" "$is_day")"
condition="$(condition_text "$code")"
temp="${temp_num}${unit_suffix}"
feels="${feels_num}${unit_suffix}"
wind="${wind_num} ${wind_suffix}"
[[ -z "$name" ]] && name="Weather"
text="$icon $temp"

forecast_days="$(
  jq -c '
    [.daily.time, .daily.weather_code, .daily.temperature_2m_max, .daily.temperature_2m_min] as $d |
    [range(1; ([4, ($d[0] | length)] | min)) | {
      day: ($d[0][.] | strptime("%Y-%m-%d") | mktime | strftime("%a") | ascii_upcase),
      icon: ($d[1][.] | tostring),
      high: ($d[2][.] | round | tostring),
      low: ($d[3][.] | round | tostring)
    }]
  ' <<<"$raw" 2>/dev/null || printf '[]'
)"

mkdir -p "$(dirname "$cache_file")"
jq -cn \
  --arg source "$cache_source" \
  --arg text "$text" \
  --arg location "$name" \
  --arg condition "$condition" \
  --arg temp "$temp" \
  --arg feels "$feels" \
  --arg wind "$wind" \
  --arg humidity "${humidity}%" \
  --arg forecast "$forecast" \
  --argjson forecastDays "$forecast_days" \
  '{source:$source,text:$text,location:$location,condition:$condition,temp:$temp,feels:$feels,wind:$wind,humidity:$humidity,forecast:$forecast,forecastDays:$forecastDays}' |
  tee "$cache_file"

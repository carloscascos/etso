# Database Schema Notes for OBSERVATORIO ETS

## Key Tables and Relationships

### Core Tables
- **escalas**: Main port call records (ALWAYS filter with port_trace on imo)
- **port_trace**: Container vessel filter (PRIMARY KEY: imo)
- **v_fleet**: Fleet information where `fleet = 'containers'` and `group` contains shipping company
- **ports**: Port information (portname, country, zone, portcode)
- **v_MRV**: CO2 emissions data (co2nm = CO2 kg per nautical mile)

### Escalas Table Structure
- **Primary Keys**: (start, imo)
- **portname**: Current port of call
- **start/end**: Port call start and end timestamps
- **prev_port**: Previous port in the voyage
- **next_port**: Next port in the voyage  
- **prev_leg**: Distance in nautical miles from previous port
- **next_leg**: Distance in nautical miles to next port
- **imo**: Vessel identifier

### Escalas_metrics Table
- **Same Primary Key**: (start, imo) - links directly to escalas
- Contains additional metrics and calculated values

### Query Patterns

#### Container Vessel Filtering (REQUIRED)
```sql
FROM escalas e
JOIN port_trace pt ON pt.imo = e.imo
JOIN v_fleet f ON e.imo = f.imo
WHERE f.fleet = 'containers'
```

#### Vessel Selection Methods
1. **By IMO (most reliable)**:
   ```sql
   AND e.imo = 1016654
   ```

2. **By Shipping Company**:
   ```sql
   AND f.group LIKE '%MSC%'  -- or '%Maersk%', etc.
   ```

3. **By Vessel Name (less reliable)**:
   ```sql
   AND f.name LIKE '%MSC LEILA%'
   ```

#### Route Analysis Patterns
- **Port sequences**: Use prev_port → portname → next_port
- **Distance analysis**: Use prev_leg and next_leg for nautical miles
- **Time analysis**: Use start/end timestamps for port call duration
- **Geographic analysis**: JOIN with ports table for country/zone info

#### Fuel/Emissions Analysis
```sql
LEFT JOIN v_MRV m ON e.imo = m.imo
-- m.co2nm = CO2 kg per nautical mile
-- m.foctd = Fuel Oil Consumption Total Distillate
```

### Data Availability Notes
- Container vessel data spans multiple years
- MSC LEILA example: 2025-06-21 to 2025-08-19 (9 records)
- Always check date ranges before building validation queries

### Validation Query Best Practices
1. Always join escalas with port_trace for container vessels only
2. Use IMO numbers when possible for vessel identification
3. Use proper date formatting: 'YYYY-MM-DD'
4. Consider route patterns using prev_port/next_port chains
5. Include distance metrics (prev_leg/next_leg) for route analysis
6. Join with ports for geographic grouping (country, zone)
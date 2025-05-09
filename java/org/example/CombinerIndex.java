package org.example;
import java.io.IOException;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;
import java.util.Map;
import java.util.HashMap;
public class CombinerIndex extends Reducer<Text, Text, Text, Text> {
    private final Text result = new Text();

    @Override
    protected void reduce(Text key, Iterable<Text> values, Context context) 
        throws IOException, InterruptedException {
        Map<String, Integer> urlCounts = new HashMap<>();

        for (Text val : values) {
 		String[] parts = val.toString().split("\\|", 2); // Split on "|"
            if (parts.length != 2) {
                // Skip invalid entries
                continue;
            }
            String url = parts[0];
            int count = Integer.parseInt(parts[1]);
            urlCounts.put(url, urlCounts.getOrDefault(url, 0) + count);
        }

        for (Map.Entry<String, Integer> entry : urlCounts.entrySet()) {
            result.set(entry.getKey() + "|" + entry.getValue());
            context.write(key, result);
        }
    }
}
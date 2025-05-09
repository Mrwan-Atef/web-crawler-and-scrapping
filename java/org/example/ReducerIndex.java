package org.example;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;
import java.io.IOException;
import java.util.Map;
import java.util.HashMap;
public class ReducerIndex extends Reducer<Text, Text, Text, Text> {
    private final Text output = new Text();

    @Override
    protected void reduce(Text key, Iterable<Text> values, Context context) 
        throws IOException, InterruptedException {
        Map<String, Integer> urlCounts = new HashMap<>();

        for (Text val : values) {
            String[] parts = val.toString().split("\\|", 2); // Escape the pipe
            if (parts.length != 2) {
                System.err.println("Invalid value format: " + val);
                continue;
            }
            String url = parts[0];
            int count = Integer.parseInt(parts[1]);
            urlCounts.put(url, urlCounts.getOrDefault(url, 0) + count);
        }

        if (urlCounts.isEmpty()) return;

        StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, Integer> entry : urlCounts.entrySet()) {
            sb.append(entry.getKey()).append("|").append(entry.getValue()).append("; ");
        }
        sb.setLength(sb.length() - 2); // Remove trailing "; "
        output.set(sb.toString());
        context.write(key, output);
    }
}
import json
import sys

def fix_swagger_host(swagger_data, host_value='localhost'):
    # Set a valid host value
    swagger_data['host'] = host_value

def add_consumes_for_all_paths(swagger_data, consumes_type):
    # Loop through all paths in the Swagger data
    for path in swagger_data.get('paths', {}).keys():
        # Loop through all HTTP methods for the path
        for method in swagger_data['paths'][path].keys():
            # Add consumes only if it doesn't exist
            if 'consumes' not in swagger_data['paths'][path][method]:
                swagger_data['paths'][path][method]['consumes'] = [consumes_type]

def add_produces_for_all_paths(swagger_data, produces_type):
    # Loop through all paths in the Swagger data
    for path in swagger_data.get('paths', {}).keys():
        # Loop through all HTTP methods for the path
        for method in swagger_data['paths'][path].keys():
            # Add produces only if it doesn't exist
            if 'produces' not in swagger_data['paths'][path][method]:
                swagger_data['paths'][path][method]['produces'] = [produces_type]

def extract_common_base_path(paths):
    # Find the common base path among all paths
    common_base_path = min(paths, key=lambda x: len(x.split('/')))

    # Remove trailing part after the first path segment
    common_base_path = '/' + '/'.join(common_base_path.split('/')[1:-1])

    return common_base_path

def convert_to_swagger2(input_file, output_file, host_value='localhost'):
    # Read Postman Collection JSON from input file
    with open(input_file, 'r') as f:
        postman_data = json.load(f)

    # Extract relevant components from Postman data
    info = postman_data.get('info', {})
    item = postman_data.get('item', [])
    tags = postman_data.get('tag', [])  # Extract tags from Postman collection

    # Extract paths from Postman items
    paths = {}
    for postman_item in item:
        request = postman_item.get('request', {})
        url = request.get('url', {})
        path_parts = url.get('path', [])

        # Handle cases where the path is a list
        path = '/' + '/'.join(str(part) for part in path_parts if part)

        method = request.get('method', '').lower()

        if path and method:
            if path not in paths:
                paths[path] = {}

            paths[path][method] = {
                'summary': postman_item.get('name', ''),
                'responses': {'200': {'description': 'Successful response'}}
            }

            # Extract query parameters
            parameters = []
            for param in url.get('query', []):
                parameters.append({
                    'name': param.get('key', ''),
                    'in': 'query',
                    'type': 'string',  # You may adjust the type as needed
                    'description': param.get('description', '')
                })

            if parameters:
                paths[path][method]['parameters'] = parameters

    # Remove the properties not compatible with OpenAPI Specification
    info.pop('_exporter_id', None)
    info.pop('_postman_id', None)
    info.pop('schema', None)

    # Extract common base path from the paths
    common_base_path = extract_common_base_path(paths)

    # Create a copy of the keys before iteration
    paths_copy = dict(paths)
    for old_path in paths_copy.keys():
        # Remove the common base path from the paths
        new_path = old_path.replace(common_base_path, '', 1)
        paths[new_path] = paths.pop(old_path)

    # Check if paths in the output Swagger document have a leading "/"
    for path in list(paths.keys()):
        if not path.startswith('/'):
            paths['/' + path] = paths.pop(path)

    # Convert Postman Collection to Swagger 2.0
    swagger_data = {
        'swagger': '2.0',
        'info': {
            'description': info.get('description', ''),
            'version': info.get('version', ''),
            'title': info.get('name', ''),
            'termsOfService': 'http://swagger.io/terms/'
        },
        'host': host_value,  # Set the host value directly
        'basePath': common_base_path,  # Set the basePath to the common base path
        'schemes': ['https', 'http'],  # Add 'https' and 'http' to the schemes
        'paths': paths,
        'tags': [{'name': tag['name'], 'description': tag.get('description', '')} for tag in tags],  # Include tags from Postman collection
    }

    # Add consumes: application/json and produces: application/json for every path
    add_consumes_for_all_paths(swagger_data, "application/json")
    add_produces_for_all_paths(swagger_data, "application/json")

    # Write Swagger 2.0 JSON to output file
    with open(output_file, 'w') as f:
        json.dump(swagger_data, f, indent=2)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python script.py input_file output_file host_value")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    host_value = sys.argv[3]

    convert_to_swagger2(input_file, output_file, host_value=host_value)

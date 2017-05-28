#version 150

// Uniform inputs
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;

// Vertex inputs
in vec4 p3d_Vertex;

// Output to fragment shader
out vec4 vertex_position;

void main()
{
  gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
  vertex_position = p3d_Vertex.xyzw;
}